import json

from hm_pyhelper.diagnostics import DiagnosticsReport, Diagnostic
from hw_diag.tasks import perform_hw_diagnostics


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


def compose_diagnostics_report_from_err_msg(diagnostic_key: str, err_msg: str) -> DiagnosticsReport:
    diagnostics_report = DiagnosticsReport()
    diagnostic = Diagnostic(diagnostic_key, diagnostic_key)
    diagnostics_report.record_failure(err_msg, diagnostic)
    return diagnostics_report
