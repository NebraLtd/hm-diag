from hm_pyhelper.diagnostics.diagnostic import Diagnostic

KEY = 'PF'
FRIENDLY_NAME = "legacy_pass_fail"
CHECK_KEYS = ["ECC", "E0", "BT", "LOR"]


class PfDiagnostic(Diagnostic):
    def __init__(self):
        super(PfDiagnostic, self).__init__(KEY, FRIENDLY_NAME)

    def perform_test(self, diagnostics_report):
        def get_result(key):
            return key in diagnostics_report and \
                   diagnostics_report[key]

        all_passed = all(map(get_result, CHECK_KEYS))

        if all_passed:
            diagnostics_report.record_result(True, self)
        else:
            diagnostics_report.record_failure(False, self)
