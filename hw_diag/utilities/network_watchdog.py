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

WATCHDOG_LOG_FILE_NAME = '/var/data/watchdog.log'
LAST_RESTART_FILE_NAME = '/var/data/last_restart.txt'
MAX_LOG_SIZE = 10 * 1024 * 1024                                             # 10 Mb
LAST_RESTART_DATE_FORMAT = '%d/%m/%Y %H:%M:%S'

# Full system reboot limited to once a day
REBOOT_LIMIT_HOURS = 24
# Failed connectivity count for the network manager to restart
NM_RESTART_THRESHOLD = int(os.environ.get("NM_RESTART_THRESHOLD", 1))   # rollback back to 3
# Failed connectivity count for the hotspot to reboot
FULL_REBOOT_THRESHOLD = int(os.environ.get("NM_RESTART_THRESHOLD", 3))  # rollback back to 6

# Public DNS server for checking internet connectivity
PUBLIC_DNS_SERVER = "8.8.8.8"
PUBLIC_DNS_PORT = 53

# Add rotating log handler to the logger
logger = get_logger(__name__)
handler = RotatingFileHandler(WATCHDOG_LOG_FILE_NAME, maxBytes=MAX_LOG_SIZE, backupCount=3)
handler.setLevel(logging.INFO)
logger.addHandler(handler)


class NetworkWatchdog:
    # Static variable for saving the lost connectivity count
    lost_count = 0

    def __init__(self):
        self.systemd_proxy = Systemd()
        self.network_manager_unit = self.systemd_proxy.get_unit(DBusIds.NETWORK_MANAGER_UNIT_NAME)
        self.network_manager = NetworkManager()

    def _have_internet(self) -> bool:
        try:
            sock = socket.create_connection((PUBLIC_DNS_SERVER, PUBLIC_DNS_PORT))
            if sock:
                sock.close()
            return True
        except OSError:
            pass
        return False

    def is_connected(self) -> bool:
        logger.info("Checking the network connectivity.")

        # Log more details about the network connectivity and internet connectivity
        logger.info(f"Network manager connectivity: {self.network_manager.get_connect_state()}")
        logger.info(f"Internet connectivity: {self._have_internet()}")

        nm_connected = self.network_manager.is_connected()
        return nm_connected

    def restart_network_manager(self):
        """Restart hostOS NetworkManager service"""
        mm_restarted = self.network_manager_unit.wait_restart()
        logger.info(f"modem manager restarted: {mm_restarted}")

    def get_last_restart(self) -> datetime:
        last_restart_file = None
        try:
            last_restart_file = open(LAST_RESTART_FILE_NAME)
            return datetime.strptime(last_restart_file.read(), LAST_RESTART_DATE_FORMAT)
        except Exception as e:
            logger.info(f"Can not find the previous restart time: {e}")
            return datetime.min
        finally:
            try:
                if last_restart_file:
                    last_restart_file.close()
            except Exception as e:
                logger.info(f"Can not close the file: {e}")
                pass

    def save_last_restart(self) -> None:
        with open(LAST_RESTART_FILE_NAME, 'w') as last_restart_file:
            last_restart_file.write("\n" + datetime.now().strftime(LAST_RESTART_DATE_FORMAT))
            last_restart_file.close()

    def run_watchdog(self) -> None:
        logger.info("Running the watchdog...")

        if self.is_connected():
            self.lost_count = 0
            logger.info("Network is working.")
        else:
            self.lost_count += 1
            logger.warning(f"Network is not connected! Lost connectivity count={self.lost_count}")

            if self.lost_count > NM_RESTART_THRESHOLD:
                logger.warning(
                    "Reached out to the lost connectivity count to restart the network manager.")
                self.restart_network_manager()
                logger.info("Restarted the network connection.")

                if self.is_connected():
                    self.lost_count = 0
                    logger.info("Network is working after restarting the network connection.")
                else:
                    logger.warning("Network is still not working.")

                    if self.lost_count > FULL_REBOOT_THRESHOLD:
                        logger.warning(
                            "Reached out to the lost connectivity count to reboot the hotspot.")
                        if datetime.now() - timedelta(
                                hours=REBOOT_LIMIT_HOURS) < self.get_last_restart():
                            logger.info(
                                "Hotspot has already been restarted within a day, skipping.")
                        else:
                            self.save_last_restart()
                            logger.info("Rebooting the hotspot.")

                            balena_supervisor = BalenaSupervisor.new_from_env()
                            balena_supervisor.reboot(force=True)
