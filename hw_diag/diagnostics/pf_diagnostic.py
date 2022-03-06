from hm_pyhelper.diagnostics import DiagnosticsReport
from hm_pyhelper.diagnostics.diagnostic import Diagnostic


class PfDiagnostic(Diagnostic):
    # Diagnostics keys
    KEY = 'PF'
    FRIENDLY_NAME = "legacy_pass_fail"

    CHECK_KEYS = ["ECC", "E0", "BT", "LOR"]

    def __init__(self):
        super(PfDiagnostic, self).__init__(self.KEY, self.FRIENDLY_NAME)

    def perform_test(self, diagnostics_report: DiagnosticsReport) -> None:
        def get_result(key) -> bool:
            return key in diagnostics_report and \
                   diagnostics_report[key]

        all_passed = all(map(get_result, self.CHECK_KEYS))

        if all_passed:
            diagnostics_report.record_result(True, self)
        else:
            diagnostics_report.record_failure(False, self)
