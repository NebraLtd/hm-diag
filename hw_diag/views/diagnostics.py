import json
import base64
import os
import logging

from flask import Blueprint
from flask import render_template
from flask import jsonify
from datetime import datetime

from hw_diag.cache import cache
from hm_pyhelper.diagnostics.diagnostics_report import DiagnosticsReport
from hw_diag.diagnostics.ecc_diagnostic import EccDiagnostic
from hw_diag.diagnostics.env_var_diagnostics import EnvVarDiagnostics
from hw_diag.diagnostics.mac_diagnostics import MacDiagnostics
from hw_diag.diagnostics.serial_number_diagnostic import SerialNumberDiagnostic
from hw_diag.diagnostics.bt_diagnostic import BtDiagnostic
from hw_diag.diagnostics.lte_diagnostic import LteDiagnostic
from hw_diag.diagnostics.lora_diagnostic import LoraDiagnostic
from hw_diag.diagnostics.pf_diagnostic import PfDiagnostic
from hw_diag.diagnostics.key_diagnostics import KeyDiagnostics
from hw_diag.diagnostics.nebra_json_diagnostics import NebraJsonDiagnostics
from hw_diag.diagnostics.add_gateway_txn.gen_add_gateway_txn_diagnostic \
    import GenAddGatewayTxnDiagnostic
from hw_diag.diagnostics.add_gateway_txn.ack_add_gateway_txn_diagnostic \
    import AckAddGatewayTxnDiagnostic
from hw_diag.utilities.hardware import should_display_lte
from hw_diag.tasks import perform_hw_diagnostics
from hm_pyhelper.logger import get_logger
from hm_pyhelper.constants.shipping import DESTINATION_ADD_GATEWAY_TXN_KEY, DESTINATION_WALLETS_KEY

logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"))

LOGGER = get_logger(__name__)
DIAGNOSTICS = Blueprint('DIAGNOSTICS', __name__)
API_VERSION = 'v1'


def read_diagnostics_file():
    diagnostics = {}

    try:
        perform_hw_diagnostics()
        with open('diagnostic_data.json', 'r') as f:
            diagnostics = json.load(f)
    except FileNotFoundError:
        msg = 'Diagnostics have not yet run, please try again in a few minutes'
        diagnostics = {'error': msg}
    except Exception as e:
        msg = 'Diagnostics has encountered an error: %s'
        diagnostics = {'error': msg % str(e)}

    return diagnostics


@DIAGNOSTICS.route('/json')
@cache.cached(timeout=60)
def get_diagnostics_json():
    diagnostics = read_diagnostics_file()
    response = jsonify(diagnostics)
    response.headers.set('Content-Disposition',
                         'attachment;filename=nebra-diag.json'
                         )
    return response


@DIAGNOSTICS.route('/')
@cache.cached(timeout=60)
def get_diagnostics():
    diagnostics = read_diagnostics_file()
    display_lte = should_display_lte(diagnostics)
    now = datetime.utcnow()

    return render_template(
        'diagnostics_page.html',
        diagnostics=diagnostics,
        display_lte=display_lte,
        now=now
    )


@DIAGNOSTICS.route('/initFile.txt')
@cache.cached(timeout=15)
def get_initialisation_file():
    """
    This needs to be generated as quickly as possible,
    so we bypass the regular timer.
    """

    diagnostics = [
        SerialNumberDiagnostic(),
        EccDiagnostic(),
        MacDiagnostics(),
        EnvVarDiagnostics(),
        BtDiagnostic(),
        LteDiagnostic(),
        LoraDiagnostic(),
        KeyDiagnostics(),
        # This will overwrite any environment variables that are also defined in nebra.json
        NebraJsonDiagnostics(),
        # Must be last, it depends on previous results
        PfDiagnostic()
    ]
    diagnostics_report = DiagnosticsReport(diagnostics)
    diagnostics_report.perform_diagnostics()
    LOGGER.debug("Full diagnostics report is: %s" % diagnostics_report)

    diagnostics_str = str(json.dumps(diagnostics_report))
    response_b64 = base64.b64encode(diagnostics_str.encode('ascii'))
    return response_b64


@DIAGNOSTICS.route(f'/{API_VERSION}/gen_add_gateway_txn', methods=['POST'])
def gen_add_gateway_txn():
    """
    This needs to be generated as quickly as possible,
    so we bypass the regular timer.
    """

    diagnostics = [
        GenAddGatewayTxnDiagnostic(),
    ]
    diagnostics_report = DiagnosticsReport(diagnostics)
    diagnostics_report.perform_diagnostics()
    if diagnostics_report.has_errors({DESTINATION_ADD_GATEWAY_TXN_KEY}):
        http_code = 406
    else:
        http_code = 200

    LOGGER.debug("gen_add_gateway_txn result: %s" % diagnostics_report)

    return diagnostics_report, http_code


@DIAGNOSTICS.route(f'/{API_VERSION}/ack_add_gateway_txn', methods=['POST'])
def ack_add_gateway_txn():
    """
    This needs to be generated as quickly as possible,
    so we bypass the regular timer.
    """

    diagnostics = [
        AckAddGatewayTxnDiagnostic(),
    ]
    diagnostics_report = DiagnosticsReport(diagnostics)
    diagnostics_report.perform_diagnostics()
    if diagnostics_report.has_errors({DESTINATION_WALLETS_KEY}):
        http_code = 406
    else:
        http_code = 200

    LOGGER.debug("gen_add_gateway_txn result: %s" % diagnostics_report)

    return diagnostics_report, http_code


@DIAGNOSTICS.route('/version')
@cache.cached(timeout=60)
def version_information():
    response = {
        'firmware_version': os.getenv('FIRMWARE_VERSION', 'unknown'),
        'diagnostics_version': os.getenv('DIAGNOSTICS_VERSION', 'unknown'),
        'firmware_short_hash': os.getenv('FIRMWARE_SHORT_HASH', 'unknown'),
    }

    return response
