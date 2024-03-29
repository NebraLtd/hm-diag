from hm_pyhelper.diagnostics import DiagnosticsReport
from hm_pyhelper.diagnostics.diagnostic import Diagnostic
from hw_diag.utilities.hardware import lora_module_test


class LoraDiagnostic(Diagnostic):
    # Diagnostics keys
    KEY = 'LOR'
    FRIENDLY_NAME = "lora"

    def __init__(self):
        super(LoraDiagnostic, self).__init__(self.KEY, self.FRIENDLY_NAME)

    def perform_test(self, diagnostics_report: DiagnosticsReport) -> None:
        if lora_module_test():
            diagnostics_report.record_result(True, self)
        else:
            diagnostics_report.record_failure(False, self)
