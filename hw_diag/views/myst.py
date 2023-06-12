import logging
import os
import time

from flask import Blueprint
from flask import render_template

from hm_pyhelper.logger import get_logger
from hw_diag.utilities.auth import authenticate
from hw_diag.utilities.auth import commercial_fleet_only
from hw_diag.utilities.diagnostics import read_diagnostics_file


logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"))

LOGGER = get_logger(__name__)
MYST = Blueprint('MYST', __name__)


@MYST.route('/myst')
@authenticate
@commercial_fleet_only
def get_myst_dashboard():
    diagnostics = read_diagnostics_file()
    now = round(time.time())
    
    return render_template(
        'myst.html',
        diagnostics=diagnostics,
        now=now
    )
