import json
import base64
import os
import logging
from os import path
from datetime import datetime, timedelta


from flask import Blueprint
from flask import render_template
from flask import request
from flask import jsonify

from hw_diag.cache import cache
from hm_pyhelper.miner_param import get_ethernet_addresses
from hm_pyhelper.miner_param import get_public_keys_rust
from hm_pyhelper.miner_param import get_gateway_mfr_test_result
from hw_diag.utilities.hardware import should_display_lte
from hw_diag.utilities.hardware import get_rpi_serial
from hw_diag.utilities.hardware import lora_module_test
from hw_diag.utilities.hardware import set_diagnostics_bt_lte
from hw_diag.utilities.shell import get_environment_var
from hw_diag.tasks import perform_hw_diagnostics

logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"))

DIAGNOSTICS = Blueprint('DIAGNOSTICS', __name__)


def read_diagnostics_file():
    diagnostics = {}

    try:
        perform_hw_diagnostics()
        with open('diagnostic_data.json', 'r') as f:
            diagnostics = json.load(f)
    except FileNotFoundError:
        msg = 'Diagnostics have not yet run, please try again in a few minutes'
        diagnostics = {'error': msg}
    return diagnostics


@DIAGNOSTICS.route('/')
@cache.cached(timeout=120)
def get_diagnostics():
    diagnostics = read_diagnostics_file()

    if request.args.get('json'):
        response = jsonify(diagnostics)
        response.headers.set('Content-Disposition',
                             'attachment;filename=nebra-diag.json'
                             )
        return response

    display_lte = should_display_lte(diagnostics)

    return render_template(
        'diagnostics_page.html',
        diagnostics=diagnostics,
        display_lte=display_lte
    )


@DIAGNOSTICS.route('/initFile.txt')
@cache.cached(timeout=15)
def get_initialisation_file():
    """
    This needs to be generated as quickly as possible,
    so we bypass the regular timer.
    """

    diagnostics = {}
    get_rpi_serial(diagnostics)
    get_ethernet_addresses(diagnostics)
    get_environment_var(diagnostics)
    set_diagnostics_bt_lte(diagnostics)
    ecc_tests = get_gateway_mfr_test_result()
    public_keys = get_public_keys_rust()

    if ecc_tests['result'] == 'pass':
        diagnostics["ECC"] = True
    else:
        return 'ECC tests failed', 503

    if lora_module_test():
        diagnostics["LOR"] = True
    else:
        return 'LoRa Module is not ready', 503

    if (
            diagnostics["ECC"]
            and diagnostics["E0"]
            and diagnostics["W0"]
            and diagnostics["BT"]
            and diagnostics["LOR"]
    ):
        diagnostics["PF"] = True
    else:
        diagnostics["PF"] = False

    try:
        diagnostics['OK'] = public_keys['key']
        diagnostics['PK'] = public_keys['key']
    except KeyError:
        return 'Internal Server Error', 500

    response = {
        "VA": diagnostics['VA'],
        "FR": diagnostics['FR'],
        "E0": diagnostics['E0'],
        "W0": diagnostics['W0'],
        "RPI": diagnostics['RPI'],
        "OK": diagnostics['OK'],
        "PK": diagnostics['PK'],
        "PF": diagnostics["PF"],
        "ID": diagnostics["ID"]
    }

    response_b64 = base64.b64encode(str(json.dumps(response)).encode('ascii'))
    return response_b64
