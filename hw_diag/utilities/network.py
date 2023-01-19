import logging

from sqlalchemy.exc import NoResultFound

from hw_diag.utilities.balena_supervisor import BalenaSupervisor
from hw_diag.database import get_db_session
from hw_diag.database.models.auth import AuthKeyValue


def get_device_hostname():
    try:
        balena_supervisor = BalenaSupervisor.new_from_env()
        device_config = balena_supervisor.get_device_config()
        network = device_config.get('network')
        hostname = network.get('hostname')
    except Exception:
        hostname = None
    return hostname


def setup_hostname():
    # This runs before the Flask app is really fully running, so we do not have the
    # global "g" object with the db session, so we must spawn our own.
    db = get_db_session()
    HOSTNAME_SET_KEY = 'hostname_set'
    try:
        try:
            hostname_set_row = db.query(AuthKeyValue). \
                filter(AuthKeyValue.key == HOSTNAME_SET_KEY). \
                one()
        except NoResultFound:
            hostname_set_row = AuthKeyValue(
                key=HOSTNAME_SET_KEY,
                value='false'
            )
            db.add(hostname_set_row)
            db.commit()

        # We don't use boolean here because the field in the DB is a string as we have
        # some general key value pair table with string values. Sorry bros :-(
        if hostname_set_row.value == 'false':
            logging.info("Hostname not set yet...")
        else:
            logging.info("Hostname already set!")
    finally:
        db.close_all()
