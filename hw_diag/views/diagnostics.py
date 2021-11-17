import json
import base64
import os
import logging

from flask import Blueprint
from flask import render_template
from flask import jsonify

from hw_diag.cache import cache
from hm_pyhelper.diagnostics.diagnostics_report import DiagnosticsReport
from hw_diag.diagnostics.ecc_diagnostic import EccDiagnostic
from hw_diag.diagnostics.env_var_diagnostics import EnvVarDiagnostics
from hw_diag.diagnostics.mac_diagnostics import MacDiagnostics
from hw_diag.diagnostics.serial_number_diagnostic import SerialNumberDiagnostic
from hw_diag.diagnostics.bt_lte_diagnostic import BtLteDiagnostics
from hw_diag.diagnostics.lora_diagnostic import LoraDiagnostic
from hw_diag.diagnostics.pf_diagnostic import PfDiagnostic
from hw_diag.diagnostics.key_diagnostics import KeyDiagnostics
from hw_diag.utilities.hardware import should_display_lte
from hw_diag.tasks import perform_hw_diagnostics
from hm_pyhelper.logger import get_logger

logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"))

LOGGER = get_logger(__name__)
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

    diagnostics = [
        SerialNumberDiagnostic(),
        EccDiagnostic(),
        MacDiagnostics(),
        EnvVarDiagnostics(),
        BtLteDiagnostics(),
        LoraDiagnostic(),
        KeyDiagnostics(),
        # Must be last, it depends on previous results
        PfDiagnostic()
    ]
    diagnostics_report = DiagnosticsReport(diagnostics)
    diagnostics_report.perform_diagnostics()
    LOGGER.debug("Full diagnostics report is: %s" % diagnostics_report)

    diagnostics_str = str(json.dumps(diagnostics_report))
    response_b64 = base64.b64encode(diagnostics_str.encode('ascii'))
    return response_b64
