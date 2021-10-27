from hm_pyhelper.diagnostics.diagnostic import Diagnostic
from hw_diag.utilities.hardware import lora_module_test

KEY = 'LOR'
FRIENDLY_NAME = "lora"


class LoraDiagnostic(Diagnostic):
    def __init__(self):
        super(LoraDiagnostic, self).__init__(KEY, FRIENDLY_NAME)

    def perform_test(self, diagnostics_report):
        if lora_module_test():
            diagnostics_report.record_result(True, self)
        else:
            diagnostics_report.record_failure(False, self)
