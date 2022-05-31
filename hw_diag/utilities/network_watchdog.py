import logging
import os
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
import socket

from hm_pyhelper.logger import get_logger
from hw_diag.utilities.balena_supervisor import BalenaSupervisor
from hw_diag.utilities.dbus_proxy.dbus_ids import DBusIds
from hw_diag.utilities.dbus_proxy.network_manager import NetworkManager
from hw_diag.utilities.dbus_proxy.systemd import Systemd
from hw_diag.utilities.keystore import KeyStore


class NetworkWatchdog:
    VOLUME_PATH = '/var/watchdog/'
    TMP_PATH = '/tmp/'
    WATCHDOG_LOG_FILE_NAME = 'watchdog.log'
    LAST_RESTART_FILE_NAME = 'last_restart.json'

    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 Mb
    LAST_RESTART_KEY = 'last_restart'
    LAST_RESTART_DATE_FORMAT = '%d/%m/%Y %H:%M:%S'

    # Full system reboot limited to once a day
    REBOOT_LIMIT_HOURS = 24
    # Failed connectivity count for the network manager to restart
    NM_RESTART_THRESHOLD = int(os.environ.get("NM_RESTART_THRESHOLD", 1))  # rollback back to 3
    # Failed connectivity count for the hotspot to reboot
    FULL_REBOOT_THRESHOLD = int(os.environ.get("NM_RESTART_THRESHOLD", 3))  # rollback back to 6

    # Public DNS server for checking internet connectivity
    PUBLIC_DNS_SERVER = "8.8.8.8"
    PUBLIC_DNS_PORT = 53

    # Static variable for saving the lost connectivity count
    lost_count = 0

    def __init__(self):
        if os.access(self.VOLUME_PATH, os.W_OK):
            self.log_file_path = os.path.join(self.VOLUME_PATH, self.WATCHDOG_LOG_FILE_NAME)
            self.state_file_path = os.path.join(self.VOLUME_PATH, self.LAST_RESTART_FILE_NAME)
        elif os.access(self.TMP_PATH, os.W_OK):
            self.log_file_path = os.path.join(self.TMP_PATH, self.WATCHDOG_LOG_FILE_NAME)
            self.state_file_path = os.path.join(self.TMP_PATH, self.LAST_RESTART_FILE_NAME)
        else:
            raise Exception('Could not find a writable volume path.')

        # Set up logger
        self.logger = get_logger(__name__)
        # Add rotating log handler to the logger
        handler = RotatingFileHandler(self.log_file_path, maxBytes=self.MAX_LOG_SIZE, backupCount=3)
        handler.setLevel(logging.INFO)
        self.logger.addHandler(handler)

        self.systemd_proxy = Systemd()
        self.network_manager_unit = self.systemd_proxy.get_unit(DBusIds.NETWORK_MANAGER_UNIT_NAME)
        self.network_manager = NetworkManager()

    def have_internet(self) -> bool:
        try:
            sock = socket.create_connection((self.PUBLIC_DNS_SERVER, self.PUBLIC_DNS_PORT))
            if sock:
                sock.close()
            return True
        except OSError:
            pass
        return False

    def is_connected(self) -> bool:
        self.logger.info("Checking the network connectivity.")

        # Log more details about the network connectivity and internet connectivity
        self.logger.info(f"Network manager state: {self.network_manager.get_connect_state()}")
        self.logger.info(f"Internet connectivity: {self.have_internet()}")

        nm_connected = self.network_manager.is_connected()
        return nm_connected

    def restart_network_manager(self):
        """Restart hostOS NetworkManager service"""
        mm_restarted = self.network_manager_unit.wait_restart()
        self.logger.info(f"modem manager restarted: {mm_restarted}")

    def get_last_restart(self) -> datetime:
        try:
            last_restart = KeyStore(self.state_file_path).get(self.LAST_RESTART_KEY)
            return datetime.strptime(last_restart, self.LAST_RESTART_DATE_FORMAT)
        except Exception as e:
            self.logger.info(f"Can not find the previous restart time: {e}")
            return datetime.min

    def save_last_restart(self) -> None:
        store = KeyStore(self.state_file_path)
        store.set(self.LAST_RESTART_KEY, datetime.now().strftime(self.LAST_RESTART_DATE_FORMAT))

    def run_watchdog(self) -> None:
        self.logger.info("Running the watchdog...")

        if self.is_connected():
            self.lost_count = 0
            self.logger.info("Network is working.")
        else:
            self.lost_count += 1
            self.logger.warning(
                f"Network is not connected! Lost connectivity count={self.lost_count}")

            if self.lost_count > self.NM_RESTART_THRESHOLD:
                self.logger.warning(
                    "Reached out to the lost connectivity count to restart the network manager.")
                self.restart_network_manager()
                self.logger.info("Restarted the network connection.")

                if self.is_connected():
                    self.lost_count = 0
                    self.logger.info("Network is working after restarting the network connection.")
                else:
                    self.logger.warning("Network is still not working.")

                    if self.lost_count > self.FULL_REBOOT_THRESHOLD:
                        self.logger.warning(
                            "Reached out to the lost connectivity count to reboot the hotspot.")
                        if datetime.now() - timedelta(
                                hours=self.REBOOT_LIMIT_HOURS) < self.get_last_restart():
                            self.logger.info(
                                "Hotspot has already been restarted within a day, skipping.")
                        else:
                            self.save_last_restart()
                            self.logger.info("Rebooting the hotspot.")

                            balena_supervisor = BalenaSupervisor.new_from_env()
                            balena_supervisor.reboot(force=True)
