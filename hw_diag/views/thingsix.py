import logging
import os
import shutil

from flask import Blueprint
from flask import render_template

from hm_pyhelper.logger import get_logger
from hw_diag.utilities.auth import authenticate
from hw_diag.utilities.auth import commercial_fleet_only
from hw_diag.utilities.db import get_value
from hw_diag.utilities.db import set_value
from hw_diag.utilities.balena_supervisor import BalenaSupervisor


logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"))

LOGGER = get_logger(__name__)
THINGSIX = Blueprint('THINGSIX', __name__)

THINGSIX_CONFIG_TEMPLATE = '/opt/thingsix/thingsix_config.yaml'
THINGSIX_CONFIG_FILE = '/var/thix/config.yaml'


@THINGSIX.route('/thingsix')
@authenticate
@commercial_fleet_only
def get_thix_dashboard():
    # If THIX isn't enabled render the setup page.
    try:
        if get_value('thix_enabled') != 'true':
            render_template('thix_setup.html')
    except Exception:
        return render_template('thix_setup.html')

    # If THIX is enabled but isn't onboarded render the onboard page.
    try:
        if get_value('thix_onboarded') != 'true':
            render_template('thix_onboard.html')
    except Exception:
        return render_template('thix_onboard.html')

    # Else just render the THIX dashboard.
    return render_template('thix_dashboard.html')


@THINGSIX.route('/thingsix/enable')
@authenticate
@commercial_fleet_only
def enable_thix():
    # Only allow this if it's currently not enabled...
    try:
        if get_value('thix_enabled') == 'true':
            return 'ThingsIX already enabled', 400
    except Exception:
        return 'ThingsIX already enabled', 400

    # Copy the config into place...
    shutil.copy(THINGSIX_CONFIG_TEMPLATE, THINGSIX_CONFIG_FILE)
    set_value('thix_enabled', 'true')
    return 'Accepted', 202
