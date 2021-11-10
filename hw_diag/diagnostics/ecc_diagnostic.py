import json
from hm_pyhelper.miner_param import get_gateway_mfr_test_result
from hm_pyhelper.diagnostics.diagnostic import Diagnostic

KEY = 'ECC'
FRIENDLY_NAME = "ECC"


class EccDiagnostic(Diagnostic):
    def __init__(self):
        super(EccDiagnostic, self).__init__(KEY, FRIENDLY_NAME)

    def perform_test(self, diagnostics_report):
        try:
            ecc_tests = get_gateway_mfr_test_result()

            if ecc_tests['result'] == 'pass':
                diagnostics_report.record_result(True, self)
            else:
                msg = "gateway_mfr test finished with error, %s" % \
                      str(json.dumps(ecc_tests))
                diagnostics_report.record_failure(msg, self)

        except Exception as e:
            diagnostics_report.record_failure(str(e), self)
