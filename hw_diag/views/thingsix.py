import logging
import os

from flask import Blueprint
from flask import render_template

from hm_pyhelper.logger import get_logger
from hw_diag.utilities.auth import authenticate
from hw_diag.utilities.auth import commercial_fleet_only
from hw_diag.utilities.db import get_value
from hw_diag.utilities.db import set_value


logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"))

LOGGER = get_logger(__name__)
THINGSIX = Blueprint('THINGSIX', __name__)


@THINGSIX.route('/thingsix')
@authenticate
@commercial_fleet_only
def get_thix_dashboard():
    # If THIX isn't enabled render the setup page.
    try:
        if not bool(get_value('thix_enabled')):
            render_template('thix_setup.html')
    except Exception:
        return render_template('thix_setup.html')

    # If THIX isn't onboarded render the onboard page.
    try:
        if not bool(get_value('thix_onboarded')):
            render_template('thix_onboard.html')
    except Exception:
        return render_template('thix_onboard.html')

    # Else just render the THIX dashboard.
    return render_template('thix_dashboard.html')
