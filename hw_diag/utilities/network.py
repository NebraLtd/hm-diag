import logging
import subprocess  # nosec

import requests
from sqlalchemy.exc import NoResultFound

from hw_diag.utilities.balena_supervisor import BalenaSupervisor
from hw_diag.database import get_db_session
from hw_diag.database.models.auth import AuthKeyValue
from hw_diag.utilities.auth import generate_default_password
from hw_diag.constants import HPT_IP


def get_wan_ip_address():
    try:
        resp = requests.get("https://icanhazip.com")  # nosec
        return resp.text
    except Exception:
        return None


def manufacturing_mode_ping_check() -> bool:
    # in manufacturing if hpt is reachable
    logging.info(f"lets ping hpt to detect network. HPT: {HPT_IP}")
    try:
        # ping without count 2s, interval  0.5s and timeout of 1s
        cmd = ["ping", "-c", "2", "-i", "0.5", "-W", "1", HPT_IP]
        res = subprocess.check_output(cmd).decode('utf8')  # nosec
        ttl = res.split('\n')[1].split('ttl=')[1].split(' ')[0]
        if ttl != '64':
            # ping reply is not from the first hop which we expect to be hpt so
            # not in manufacturing mode.
            return False

        return True
    except Exception as e:
        logging.error(f"failed to ping hpt : {HPT_IP}")
        logging.error(e)
        return False


def get_device_hostname():
    try:
        balena_supervisor = BalenaSupervisor.new_from_env()
        device_config = balena_supervisor.get_device_config()
        network = device_config.get("network")
        hostname = network.get("hostname")
    except Exception:
        hostname = None
    return hostname


def setup_hostname():
    # This runs before the Flask app is really fully running, so we do not have the
    # global "g" object with the db session, so we must spawn our own.
    db = get_db_session()
    HOSTNAME_SET_KEY = "hostname_set"
    try:
        try:
            hostname_set_row = (
                db.query(AuthKeyValue)
                .filter(AuthKeyValue.key == HOSTNAME_SET_KEY)
                .one()
            )
        except NoResultFound:
            hostname_set_row = AuthKeyValue(key=HOSTNAME_SET_KEY, value="false")
            db.add(hostname_set_row)
            db.commit()

        # We don't use boolean here because the field in the DB is a string as we have
        # some general key value pair table with string values. Sorry bros :-(
        if hostname_set_row.value == "false":
            logging.info("Hostname not set yet...")
            # Set hostname via Balena supervisor...
            default_password = generate_default_password()
            hostname_suffix = default_password[6:]
            hostname = "nebra-%s.local" % hostname_suffix
            balena_supervisor = BalenaSupervisor.new_from_env()
            balena_supervisor.set_hostname(hostname)
            hostname_set_row.value = "true"
            db.commit()
        else:
            logging.info("Hostname already set!")

        db.close_all()
    except Exception as err:
        logging.error("Error setting hostname: %s" % str(err))
        db.close_all()
    finally:
        db.close_all()
