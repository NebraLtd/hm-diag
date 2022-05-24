import time
import urllib.request
from datetime import datetime, timedelta
from hm_pyhelper.logger import get_logger
from retry.api import retry_call
from utilities.balena_supervisor import BalenaSupervisor

logging = get_logger(__name__)

RESTART_FILE_NAME = 'restarts.csv'
RESTART_DATE_FORMAT = '%d/%m/%Y %H:%M:%S'


def have_internet() -> bool:
    """wait for wait_time seconds for modem to achieve connectivity"""
    try:
        retry_call(
            urllib.request.urlopen,
            fkwargs={"url": "https://google.com", "timeout": 3},
            tries=3,
            delay=5,
            logger=logging,
        )
        return True
    except Exception as e:
        logging.info(f"Internet is not accessible: {e}")
        return False


def get_last_restart() -> datetime:
    try:
        f = open(RESTART_FILE_NAME)
        lines = f.read().splitlines()
        last_line = lines[-1]
        return datetime.strptime(last_line, RESTART_DATE_FORMAT)
    except Exception as e:
        return datetime.min
    finally:
        try:
            f.close()
        except:
            pass


def save_last_restart() -> None:
    with open(RESTART_FILE_NAME, 'a') as f:
        f.write("\n" + datetime.now().strftime(RESTART_DATE_FORMAT))
        f.close()


def reconnect_network() -> None:
    time.sleep(30)


def check_network_connectivity() -> None:
    logging.info("Checking the network connectivity.")

    if have_internet():
        logging.info("Internet is working.")
    else:
        logging.warning("Network is not connected!")

        # Reconnect network
        logging.info("Restarting the network connection.")
        reconnect_network()
        logging.info("Restarted the network connection.")

        if have_internet():
            logging.info("Internet is working after restarting the network connection.")
        else:
            logging.warning("Internet is still not working.")

            if datetime.now() - timedelta(hours=24) < get_last_restart():
                logging.info("Device has already been restarted within the last hour, skipping.")
            else:
                save_last_restart()

                logging.info("Rebooting the device.")
                balena_supervisor = BalenaSupervisor.new_from_env()
                balena_supervisor.reboot(force=True)

