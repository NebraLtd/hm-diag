from __future__ import annotations
import logging
import os
import tempfile
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
from hm_pyhelper.logger import get_logger
from icmplib import ping
from hw_diag.utilities.balena_supervisor import BalenaSupervisor
from hw_diag.utilities.dbus_proxy.dbus_ids import DBusIds
from hw_diag.utilities.dbus_proxy.network_manager import NetworkManager
from hw_diag.utilities.dbus_proxy.systemd import Systemd

LOGLEVEL = os.environ.get("LOGLEVEL", "DEBUG")
_log_format = "%(asctime)s - [%(levelname)s] - (%(filename)s:%(lineno)d) - %(message)s"


class NetworkWatchdog:
    VOLUME_PATH = '/var/watchdog/'
    WATCHDOG_LOG_FILE_NAME = 'watchdog.log'
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 Mb

    # Failed connectivity count for the network manager to restart
    NM_RESTART_THRESHOLD = int(os.environ.get("NM_RESTART_THRESHOLD", 1))
    # Failed connectivity count for the hotspot to reboot
    FULL_REBOOT_THRESHOLD = int(os.environ.get("FULL_REBOOT_THRESHOLD", 3))
    # Failed reboot count for the hotspot to reboot forcibly
    FULL_FORCE_REBOOT_THRESHOLD = int(os.environ.get("FULL_FORCE_REBOOT_THRESHOLD", 3))
    # Full system reboot limited to once a day
    REBOOT_LIMIT_HOURS = int(os.environ.get("REBOOT_LIMIT_HOURS", 24))

    PUBLIC_SERVERS = ['8.8.8.8', '1.1.1.1']       # NOSONAR

    # Static variable for saving the up time of the hotspot
    watchdog_start_time = datetime.min

    # Static variable for saving the lost connectivity count
    lost_count = 0

    # Static variable for saving the failed reboot count
    reboot_request_count = 0

    def __init__(self):
        # Save the watchdog start time
        self.watchdog_start_time = datetime.now()

        # Prepare the log file location
        if os.access(self.VOLUME_PATH, os.W_OK):
            self.log_file_path = os.path.join(self.VOLUME_PATH, self.WATCHDOG_LOG_FILE_NAME)
        else:
            self.temp_dir = tempfile.TemporaryDirectory()
            self.log_file_path = os.path.join(self.temp_dir.name, self.WATCHDOG_LOG_FILE_NAME)

        # Set up logger
        self.LOGGER = get_logger(__name__)
        # Add rotating log handler to the logger
        handler = RotatingFileHandler(self.log_file_path, maxBytes=self.MAX_LOG_SIZE, backupCount=3)
        handler.setLevel(LOGLEVEL)
        handler.setFormatter(logging.Formatter(_log_format))
        self.LOGGER.addHandler(handler)

        # Log the watchdog intro
        self.LOGGER.info("Watchdog started!")

    def __del__(self):
        if hasattr(self, 'temp_dir'):
            self.temp_dir.cleanup()

    def icmp_ping(self, ip: str) -> bool:
        try:
            ping_target = ping(ip)
            reachable = ping_target and ping_target.address == ip and ping_target.is_alive
            if reachable:
                self.LOGGER.info(f'{ip} is reachable.')
            else:
                self.LOGGER.info(f'{ip} is not reachable.')
            return reachable
        except Exception:
            return False

    def is_local_network_connected(self) -> bool:
        network_manager = NetworkManager()
        gateways = network_manager.get_gateways()
        for gateway in gateways:
            if self.icmp_ping(gateway):
                return True
        return False

    def is_internet_connected(self) -> bool:
        for public_server in self.PUBLIC_SERVERS:
            if self.icmp_ping(public_server):
                return True
        return False

    def is_connected(self) -> bool:
        is_local_network_connected = self.is_local_network_connected()
        self.LOGGER.info(f"Local network connection: {is_local_network_connected}")

        is_internet_connected = self.is_internet_connected()
        self.LOGGER.info(f"Internet connection: {is_internet_connected}")

        return is_local_network_connected

    def restart_network_manager(self) -> None:
        """Restart hostOS NetworkManager service"""
        systemd_proxy = Systemd()
        network_manager_unit = systemd_proxy.get_unit(DBusIds.NETWORK_MANAGER_UNIT_NAME)
        nm_restarted = network_manager_unit.wait_restart()
        self.LOGGER.info(f"Network manager restarted: {nm_restarted}")

    def ensure_network_connection(self) -> None:
        self.LOGGER.info("Ensuring the network connection...")

        up_time = datetime.now() - self.watchdog_start_time
        self.LOGGER.info(f"Watchdog has been up for {up_time}")

        # If network is connected, nothing to do more
        if self.is_connected():
            self.lost_count = 0
            self.LOGGER.info("Network is working.")
            return

        # If network is not working, take the next step
        self.lost_count += 1
        self.LOGGER.warning(
            f"Network is not connected! Lost connectivity count={self.lost_count}")

        if self.lost_count >= self.FULL_REBOOT_THRESHOLD:
            self.LOGGER.warning(
                "Reached threshold for system reboot to recover network.")
            if up_time < timedelta(hours=self.REBOOT_LIMIT_HOURS):
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
        elif self.lost_count >= self.NM_RESTART_THRESHOLD:
            self.LOGGER.warning(
                "Reached threshold for Network Manager restart to recover network.")
            self.restart_network_manager()


if __name__ == '__main__':
    watchdog = NetworkWatchdog()
    watchdog.ensure_network_connection()
