from __future__ import annotations

import logging
import os
import tempfile
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
import socket

from hm_pyhelper.logger import get_logger
from icmplib import traceroute, ping

from hw_diag.utilities.balena_supervisor import BalenaSupervisor
from hw_diag.utilities.dbus_proxy.dbus_ids import DBusIds
from hw_diag.utilities.dbus_proxy.network_manager import NetworkManager
from hw_diag.utilities.dbus_proxy.systemd import Systemd
from hw_diag.utilities.keystore import KeyStore

LOGLEVEL = os.environ.get("LOGLEVEL", "DEBUG")
_log_format = "%(asctime)s - [%(levelname)s] - (%(filename)s:%(lineno)d) - %(message)s"


class NetworkWatchdog:
    _instance = None

    VOLUME_PATH = '/var/watchdog/'
    WATCHDOG_LOG_FILE_NAME = 'watchdog.log'
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 Mb

    WATCHDOG_STATE_FILE_NAME = 'state.json'
    PREVIOUS_GATEWAY_KEY = 'previous_gateway'

    # Failed connectivity count for the network manager to restart
    NM_RESTART_THRESHOLD = int(os.environ.get("NM_RESTART_THRESHOLD", 1))
    # Failed connectivity count for the hotspot to reboot
    FULL_REBOOT_THRESHOLD = int(os.environ.get("FULL_REBOOT_THRESHOLD", 3))
    # Failed reboot count for the hotspot to reboot forcibly
    FULL_FORCE_REBOOT_THRESHOLD = int(os.environ.get("FULL_FORCE_REBOOT_THRESHOLD", 3))
    # Full system reboot limited to once a day
    REBOOT_LIMIT_HOURS = int(os.environ.get("REBOOT_LIMIT_HOURS", 24))

    # Public DNS server for checking internet connectivity
    PUBLIC_DNS_SERVER = "8.8.8.8"       # NOSONAR
    PUBLIC_DNS_PORT = 53

    # Static variable for saving the up time of the hotspot
    up_time = datetime.min

    # Static variable for saving the lost connectivity count
    lost_count = 0

    # Static variable for saving the failed reboot count
    reboot_request_count = 0

    @staticmethod
    def get_instance() -> NetworkWatchdog:
        """ Static method to fetch the current instance.
        """
        if not NetworkWatchdog._instance:
            NetworkWatchdog()
        return NetworkWatchdog._instance

    def __init__(self):
        """ Constructor.
               """
        if NetworkWatchdog._instance is None:
            NetworkWatchdog._instance = self
        else:
            raise RuntimeError("You cannot create another SingletonGovt class")

        # Save the uptime
        self.up_time = datetime.now()

        # Prepare the log file location
        if os.access(self.VOLUME_PATH, os.W_OK):
            self.log_file_path = os.path.join(self.VOLUME_PATH, self.WATCHDOG_LOG_FILE_NAME)
            self.state_file_path = os.path.join(self.VOLUME_PATH, self.WATCHDOG_STATE_FILE_NAME)
        else:
            self.temp_dir = tempfile.TemporaryDirectory()
            self.log_file_path = os.path.join(self.temp_dir.name, self.WATCHDOG_LOG_FILE_NAME)
            self.state_file_path = os.path.join(self.temp_dir.name, self.WATCHDOG_STATE_FILE_NAME)

        # Set up logger
        self.LOGGER = get_logger(__name__)
        # Add rotating log handler to the logger
        handler = RotatingFileHandler(self.log_file_path, maxBytes=self.MAX_LOG_SIZE, backupCount=3)
        handler.setLevel(LOGLEVEL)
        handler.setFormatter(logging.Formatter(_log_format))
        self.LOGGER.addHandler(handler)

        self.systemd_proxy = Systemd()
        self.network_manager_unit = self.systemd_proxy.get_unit(DBusIds.NETWORK_MANAGER_UNIT_NAME)
        self.network_manager = NetworkManager()

        # Log the watchdog intro
        self.LOGGER.info("Watchdog is started!")

    def __del__(self):
        if hasattr(self, 'temp_dir'):
            self.temp_dir.cleanup()

    def find_gateway_ip(self) -> str:
        hops = traceroute(self.PUBLIC_DNS_SERVER)

        """
        The local gateway IP should be the address of the 2nd hop.
        Also first hop and 2nd hop should have the different addresses,
        otherwise 2nd hop address is invalid address.
        """
        if len(hops) >= 2 and hops[0].address != hops[1].address and hops[1].is_alive:
            gateway_ip = hops[1].address
            self.LOGGER.info(f"Found local gateway {gateway_ip} using traceroute.")
            self.save_previous_gateway_ip(gateway_ip)
        else:
            self.LOGGER.info("Failed to find local gateway using traceroute.")
            gateway_ip = self.get_previous_gateway_ip()
            self.LOGGER.info(f"Previous local gateway: {gateway_ip}")

        return gateway_ip

    def save_previous_gateway_ip(self, ip: str) -> None:
        store = KeyStore(self.state_file_path)
        store.set(self.PREVIOUS_GATEWAY_KEY, ip)

    def get_previous_gateway_ip(self) -> str:
        try:
            return KeyStore(self.state_file_path).get(self.PREVIOUS_GATEWAY_KEY, '')
        except Exception:
            return ''

    def icmp_ping(self, ip: str) -> bool:
        try:
            result = ping(ip)
            return result and result.is_alive
        except Exception:
            return False

    def have_internet(self, timeout=10) -> bool:
        try:
            socket.setdefaulttimeout(timeout)
            sock = socket.create_connection((self.PUBLIC_DNS_SERVER, self.PUBLIC_DNS_PORT))
            sock.close()
            return True
        except Exception:
            return False

    def is_connected(self) -> bool:
        local_gateway_connectivity = False
        gateway_ip = self.find_gateway_ip()
        if gateway_ip:
            local_gateway_connectivity = self.icmp_ping(gateway_ip)

        # Log more details about network connection status
        self.LOGGER.info(f"Local gateway({gateway_ip}) connectivity: {local_gateway_connectivity}")
        self.LOGGER.info(f"Internet({self.PUBLIC_DNS_SERVER}) connectivity: {self.have_internet()}")

        return local_gateway_connectivity

    def restart_network_manager(self) -> None:
        """Restart hostOS NetworkManager service"""
        nm_restarted = self.network_manager_unit.wait_restart()
        self.LOGGER.info(f"Network manager restarted: {nm_restarted}")

    def ensure_network_connection(self) -> None:
        self.LOGGER.info("Ensuring the network connection...")

        # If network is connected, nothing to do more
        if self.is_connected():
            self.lost_count = 0
            self.LOGGER.info("Network is working.")
            return

        # If network is not working, take the next step
        self.lost_count += 1
        self.LOGGER.warning(
            f"Network is not connected! Lost connectivity count={self.lost_count}")

        if self.lost_count >= self.NM_RESTART_THRESHOLD:
            self.LOGGER.warning(
                "Reached threshold for nm restart for recovering network.")
            self.restart_network_manager()
            self.LOGGER.info("Restarted the network connection.")

        if self.lost_count >= self.FULL_REBOOT_THRESHOLD:
            self.LOGGER.warning(
                "Reached threshold for system reboot for recovering network.")
            if self.up_time + timedelta(
                    hours=self.REBOOT_LIMIT_HOURS) > datetime.now():
                self.LOGGER.info(
                    f"Hotspot has been restarted already within {self.REBOOT_LIMIT_HOURS}hour(s)."
                    f" Skip the rebooting.")
                return

            force_reboot = self.reboot_request_count >= self.FULL_FORCE_REBOOT_THRESHOLD

            self.LOGGER.info(f"Rebooting the hotspot(force={force_reboot}).")

            self.reboot_request_count += 1
            self.LOGGER.info(f"Reboot request count={self.reboot_request_count}.")

            balena_supervisor = BalenaSupervisor.new_from_env()
            balena_supervisor.reboot(force=force_reboot)


if __name__ == '__main__':
    watchdog = NetworkWatchdog()
    watchdog.ensure_network_connection()
