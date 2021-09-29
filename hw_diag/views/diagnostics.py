import json
import base64
import os.path
import logging

from flask import Blueprint
from flask import render_template
from flask import request
from flask import jsonify

from hm_pyhelper.miner_param import get_ethernet_addresses
from hm_pyhelper.miner_param import get_public_keys_rust
from hm_pyhelper.miner_param import get_gateway_mfr_test_result
from hw_diag.utilities.hardware import should_display_lte
from hw_diag.utilities.hardware import get_rpi_serial
from hw_diag.utilities.hardware import lora_module_test
from hw_diag.utilities.hardware import set_diagnostics_bt_lte
from hw_diag.utilities.shell import get_environment_var

logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"))

ECC_SUCCESSFUL_TOUCH_FILEPATH = "/var/data/gwmfr_ecc_provisioned"
DIAGNOSTICS = Blueprint('DIAGNOSTICS', __name__)


def read_diagnostics_file():
    diagnostics = {}
    try:
        with open('diagnostic_data.json', 'r') as f:
            diagnostics = json.load(f)
    except FileNotFoundError:
        msg = 'Diagnostics have not yet run, please try again in a few minutes'
        diagnostics = {'error': msg}
    return diagnostics


@DIAGNOSTICS.route('/')
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


def is_gwmfr_running():
    return not os.path.isfile(ECC_SUCCESSFUL_TOUCH_FILEPATH)


@DIAGNOSTICS.route('/initFile.txt')
def get_initialisation_file():
    """
    This needs to be generated as quickly as possible,
    so we bypass the regular timer.
    """

    if is_gwmfr_running():
        logging.info("hm-gwmfr is still runnning. \
            initFile.txt will not be returned.")
        return 'hm-gwmfr is still running. ECC cannot be accessed yet.', 500

    diagnostics = {}
    get_rpi_serial(diagnostics)
    get_ethernet_addresses(diagnostics)
    get_environment_var(diagnostics)
    set_diagnostics_bt_lte(diagnostics)
    ecc_tests = get_gateway_mfr_test_result()

    if ecc_tests['result'] == 'pass':
        diagnostics["ECC"] = True
    else:
        return 'ECC tests failed', 500

    if lora_module_test():
        diagnostics["LOR"] = True
    else:
        return 'LoRa Module is not ready', 500

    if (
            diagnostics["ECC"] is True
            and diagnostics["E0"] is not None
            and diagnostics["W0"] is not None
            and diagnostics["BT"] is True
            and diagnostics["LOR"] is True
    ):
        diagnostics["PF"] = True
    else:
        diagnostics["PF"] = False

    try:
        diagnostics['OK'] = get_public_keys_rust()['key']
        diagnostics['PK'] = get_public_keys_rust()['key']
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
