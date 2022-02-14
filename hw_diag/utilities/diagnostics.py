from hm_pyhelper.diagnostics import DiagnosticsReport, Diagnostic


def compose_diagnostics_report_from_err_msg(diagnostic_key: str, err_msg: str) -> DiagnosticsReport:
    diagnostics_report = DiagnosticsReport()
    diagnostic = Diagnostic(diagnostic_key, diagnostic_key)
    diagnostics_report.record_failure(err_msg, diagnostic)
    return diagnostics_report
