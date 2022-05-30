from datetime import datetime, timedelta
from hm_pyhelper.logger import get_logger
from utilities.balena_supervisor import BalenaSupervisor
from utilities.dbus_proxy.dbus_ids import DBusIds
from utilities.dbus_proxy.network_manager import NetworkManager
from utilities.dbus_proxy.systemd import Systemd

logging = get_logger(__name__)


class NetworkWatchdog:
    RESTART_FILE_NAME = 'restarts.csv'
    RESTART_DATE_FORMAT = '%d/%m/%Y %H:%M:%S'

    def __init__(self):
        self.systemd_proxy = Systemd()
        self.network_manager_unit = self.systemd_proxy.get_unit(DBusIds.NETWORK_MANAGER_UNIT_NAME)
        self.network_manager = NetworkManager()

    def restart_network_manager(self):
        """Restart hostOS NetworkManager service"""
        mm_restarted = self.network_manager_unit.wait_restart()
        logging.info(f"modem manager restarted: {mm_restarted}")

    def get_last_restart(self) -> datetime:
        try:
            f = open(self.RESTART_FILE_NAME)
            lines = f.read().splitlines()
            last_line = lines[-1]
            return datetime.strptime(last_line, self.RESTART_DATE_FORMAT)
        except Exception as e:
            logging.info(f"Can not find the previous restart time: {e}")
            return datetime.min
        finally:
            try:
                f.close()
            except Exception as e:
                logging.info(f"Can not close the file: {e}")
                pass

    def save_last_restart(self) -> None:
        with open(self.RESTART_FILE_NAME, 'a') as f:
            f.write("\n" + datetime.now().strftime(self.RESTART_DATE_FORMAT))
            f.close()

    def check_network_connectivity(self) -> None:
        logging.info("Checking the network connectivity.")

        if self.network_manager.is_connected():
            logging.info("Internet is working.")
        else:
            logging.warning("Network is not connected!")

            # Reconnect network
            logging.info("Restarting the network connection.")
            self.restart_network_manager()
            logging.info("Restarted the network connection.")

            if self.network_manager.is_connected():
                logging.info("Internet is working after restarting the network connection.")
            else:
                logging.warning("Internet is still not working.")

                if datetime.now() - timedelta(hours=24) < self.get_last_restart():
                    logging.info("Device has already been restarted within a day, skipping.")
                else:
                    self.save_last_restart()

                    logging.info("Rebooting the device.")
                    balena_supervisor = BalenaSupervisor.new_from_env()
                    balena_supervisor.reboot(force=True)
