import logging
import os

from flask import Blueprint

from hm_pyhelper.logger import get_logger
from hw_diag.utilities.auth import authenticate
from hw_diag.utilities.auth import commercial_fleet_only


logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"))

LOGGER = get_logger(__name__)
THINGSIX = Blueprint('THINGSIX', __name__)


@THINGSIX.route('/thingsix')
@authenticate
@commercial_fleet_only
def get_thix_dashboard():
    return 'Hello', 200
