import logging
import os

from flask import Blueprint
from flask import render_template
from flask import request

from hm_pyhelper.logger import get_logger
from hw_diag.utilities.auth import authenticate
from hw_diag.utilities.auth import commercial_fleet_only
from hw_diag.utilities.auth import generate_default_password
from hw_diag.utilities.ttn import write_ttn_config
from hw_diag.utilities.ttn import read_ttn_config
from hw_diag.utilities.diagnostics import read_diagnostics_file
from hw_diag.utilities.dashboard_registration import claim_miner_deeplink


logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"))

LOGGER = get_logger(__name__)
TTN = Blueprint('TTN', __name__)


@TTN.route('/ttn')
@authenticate
@commercial_fleet_only
def get_ttn_dashboard():
    diagnostics = read_diagnostics_file()
    claim_deeplink = claim_miner_deeplink()
    gateway_eui = '0000%s' % generate_default_password().upper()
    ttn_config = read_ttn_config()
    return render_template(
        'ttn_config.html',
        diagnostics=diagnostics,
        claim_deeplink=claim_deeplink,
        gateway_eui=gateway_eui,
        ttn_config=ttn_config
    )


@TTN.route('/ttn/update', methods=['POST'])
@authenticate
def update_ttn_config():
    data = request.json

    if data.get('ttn_cluster') not in ['eu', 'us', 'au']:
        return 'Bad Request', 400

    write_ttn_config(
        ttn_enabled=data.get('ttn_enabled'),
        ttn_cluster=data.get('ttn_cluster')
    )

    return 'OK', 200
