import logging
import os
import tempfile
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
import socket

from hm_pyhelper.logger import get_logger
from hw_diag.utilities.balena_supervisor import BalenaSupervisor
from hw_diag.utilities.dbus_proxy.dbus_ids import DBusIds
from hw_diag.utilities.dbus_proxy.network_manager import NetworkManager
from hw_diag.utilities.dbus_proxy.systemd import Systemd
from hw_diag.utilities.keystore import KeyStore

LOGLEVEL = os.environ.get("LOGLEVEL", "DEBUG")
_log_format = f"%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s -- %(pathname)s:(%(lineno)d) - %(message)s"  # noqa: F541 E501


class NetworkWatchdog:
    _instance = None

    VOLUME_PATH = '/var/watchdog/'
    WATCHDOG_LOG_FILE_NAME = 'watchdog.log'
    LAST_RESTART_FILE_NAME = 'last_restart.json'

    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 Mb
    LAST_RESTART_KEY = 'last_restart'
    LAST_RESTART_DATE_FORMAT = '%d/%m/%Y %H:%M:%S'

    # Full system reboot limited to once a day
    REBOOT_LIMIT_HOURS = 24
    # Failed connectivity count for the network manager to restart
    NM_RESTART_THRESHOLD = int(os.environ.get("NM_RESTART_THRESHOLD", 1))
    # Failed connectivity count for the hotspot to reboot
    FULL_REBOOT_THRESHOLD = int(os.environ.get("FULL_REBOOT_THRESHOLD", 3))
    # Failed connectivity count for the hotspot to reboot
    FULL_FORCE_REBOOT_THRESHOLD = int(os.environ.get("FULL_FORCE_REBOOT_THRESHOLD", 6))

    # Public DNS server for checking internet connectivity
    PUBLIC_DNS_SERVER = "8.8.8.8"       # NOSONAR
    PUBLIC_DNS_PORT = 53

    # Static variable for saving the lost connectivity count
    lost_count = 0

    @staticmethod
    def get_instance():
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

        if os.access(self.VOLUME_PATH, os.W_OK):
            self.log_file_path = os.path.join(self.VOLUME_PATH, self.WATCHDOG_LOG_FILE_NAME)
            self.state_file_path = os.path.join(self.VOLUME_PATH, self.LAST_RESTART_FILE_NAME)
        else:
            self.temp_dir = tempfile.TemporaryDirectory()
            self.log_file_path = os.path.join(self.temp_dir.name, self.WATCHDOG_LOG_FILE_NAME)
            self.state_file_path = os.path.join(self.temp_dir.name, self.LAST_RESTART_FILE_NAME)

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

    def have_internet(self, timeout=10) -> bool:
        try:
            socket.setdefaulttimeout(timeout)
            sock = socket.create_connection((self.PUBLIC_DNS_SERVER, self.PUBLIC_DNS_PORT))
            sock.close()
            return True
        except Exception as e:
            self.LOGGER.info(f"internet not accessible: {e}")
            return False

    def is_connected(self) -> bool:
        self.LOGGER.info("Checking the network connectivity.")

        # Log more details about the network connectivity and internet connectivity
        self.LOGGER.info(f"Network manager state: {self.network_manager.get_connect_state()}")
        self.LOGGER.info(f"Internet connectivity: {self.have_internet()}")

        nm_connected = self.network_manager.is_connected()
        return nm_connected

    def restart_network_manager(self):
        """Restart hostOS NetworkManager service"""
        nm_restarted = self.network_manager_unit.wait_restart()
        self.LOGGER.info(f"Network manager restarted: {nm_restarted}")

    def get_last_restart(self) -> datetime:
        try:
            last_restart = KeyStore(self.state_file_path).get(self.LAST_RESTART_KEY)
            return datetime.strptime(last_restart, self.LAST_RESTART_DATE_FORMAT)
        except Exception as e:
            self.LOGGER.info(f"Can not find the previous restart time: {e}")
            return datetime.min

    def save_last_restart(self) -> None:
        store = KeyStore(self.state_file_path)
        store.set(self.LAST_RESTART_KEY, datetime.now().strftime(self.LAST_RESTART_DATE_FORMAT))
        self.LOGGER.info("Saved the last_restart.")

    def ensure_network_connection(self) -> None:
        self.LOGGER.info("Running the watchdog...")

        if self.is_connected():
            self.lost_count = 0
            self.LOGGER.info("Network is working.")
        else:
            self.lost_count += 1
            self.LOGGER.warning(
                f"Network is not connected! Lost connectivity count={self.lost_count}")

            if self.lost_count > self.NM_RESTART_THRESHOLD:
                self.LOGGER.warning(
                    "Reached threshold for nm restart for recovering network.")
                self.restart_network_manager()
                self.LOGGER.info("Restarted the network connection.")

            if self.lost_count > self.FULL_REBOOT_THRESHOLD:
                self.LOGGER.warning(
                    "Reached threshold for system reboot for recovering network.")
                if datetime.now() - timedelta(
                        hours=self.REBOOT_LIMIT_HOURS) < self.get_last_restart():
                    self.LOGGER.info(
                        "Hotspot has already been restarted within a day, skipping.")
                else:
                    self.save_last_restart()

                    force_reboot = self.lost_count > self.FULL_FORCE_REBOOT_THRESHOLD

                    self.LOGGER.info(f"Rebooting the hotspot(force={force_reboot}).")
                    balena_supervisor = BalenaSupervisor.new_from_env()
                    balena_supervisor.reboot(force=force_reboot)


if __name__ == '__main__':
    print('Watchdog is running...')
    watchdog = NetworkWatchdog()
    is_connected = watchdog.is_connected()
    print("Is connected:", is_connected)
