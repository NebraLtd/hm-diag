import os
from datetime import datetime, timedelta
from hm_pyhelper.logger import get_logger
from utilities.balena_supervisor import BalenaSupervisor
from utilities.dbus_proxy.dbus_ids import DBusIds
from utilities.dbus_proxy.network_manager import NetworkManager
from utilities.dbus_proxy.systemd import Systemd

logging = get_logger(__name__)


class NetworkWatchdog:
    LAST_RESTART_FILE_NAME = '/var/data/last_restart.txt'
    LAST_RESTART_DATE_FORMAT = '%d/%m/%Y %H:%M:%S'

    # Full system reboot limited to once a day
    REBOOT_LIMIT_HOURS = 24

    # Failed connectivity count for the network manager to restart
    NM_RESTART_THRESHOLD = int(os.environ.get("NM_RESTART_THRESHOLD", 1))   # rollback back to 3

    # Failed connectivity count for the hotspot to reboot
    FULL_REBOOT_THRESHOLD = int(os.environ.get("NM_RESTART_THRESHOLD", 3))  # rollback back to 6

    def __init__(self):
        self.systemd_proxy = Systemd()
        self.network_manager_unit = self.systemd_proxy.get_unit(DBusIds.NETWORK_MANAGER_UNIT_NAME)
        self.network_manager = NetworkManager()

        # Count of lost connectivity
        self.lost_count = 0
        logging.info("Starting the network watchdog. The lost connectivity count is reset to 0.")

    def restart_network_manager(self):
        """Restart hostOS NetworkManager service"""
        mm_restarted = self.network_manager_unit.wait_restart()
        logging.info(f"modem manager restarted: {mm_restarted}")

    def get_last_restart(self) -> datetime:
        last_restart_file = None
        try:
            last_restart_file = open(self.LAST_RESTART_FILE_NAME)
            return datetime.strptime(last_restart_file.read(), self.LAST_RESTART_DATE_FORMAT)
        except Exception as e:
            logging.info(f"Can not find the previous restart time: {e}")
            return datetime.min
        finally:
            try:
                if last_restart_file:
                    last_restart_file.close()
            except Exception as e:
                logging.info(f"Can not close the file: {e}")
                pass

    def save_last_restart(self) -> None:
        with open(self.LAST_RESTART_FILE_NAME, 'w') as last_restart_file:
            last_restart_file.write("\n" + datetime.now().strftime(self.LAST_RESTART_DATE_FORMAT))
            last_restart_file.close()

    def check_network_connectivity(self) -> None:
        logging.info("Checking the network connectivity.")

        if self.network_manager.is_connected():
            self.lost_count = 0
            logging.info("Internet is working.")
        else:
            self.lost_count += 1
            logging.warning(f"Network is not connected! Lost connectivity count={self.lost_count}")

            if self.lost_count > self.NM_RESTART_THRESHOLD:
                logging.warning(
                    "Reached out to the lost connectivity count to restart the network manager.")
                self.restart_network_manager()
                logging.info("Restarted the network connection.")

                if self.network_manager.is_connected():
                    self.lost_count = 0
                    logging.info("Internet is working after restarting the network connection.")
                else:
                    logging.warning("Internet is still not working.")

                    if self.lost_count > self.FULL_REBOOT_THRESHOLD:
                        logging.warning(
                            "Reached out to the lost connectivity count to reboot the hotspot.")
                        if datetime.now() - timedelta(
                                hours=self.REBOOT_LIMIT_HOURS) < self.get_last_restart():
                            logging.info(
                                "Hotspot has already been restarted within a day, skipping.")
                        else:
                            self.save_last_restart()
                            logging.info("Rebooting the device.")

                            balena_supervisor = BalenaSupervisor.new_from_env()
                            balena_supervisor.reboot(force=True)
