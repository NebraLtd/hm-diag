import json
from hm_pyhelper.lock_singleton import ResourceBusyError
from hm_pyhelper.miner_param import LOGGER, get_gateway_mfr_test_result
from hm_pyhelper.diagnostics.diagnostic import Diagnostic
from hm_pyhelper.exceptions import ECCMalfunctionException,\
    GatewayMFRFileNotFoundException

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

        except ECCMalfunctionException as e:
            LOGGER.exception(e)
            diagnostics_report.record_failure(e, self)

        except GatewayMFRFileNotFoundException as e:
            LOGGER.exception(e)
            diagnostics_report.record_failure(e, self)

        except ResourceBusyError as e:
            LOGGER.exception(e)
            diagnostics_report.record_failure(e, self)

        except UnboundLocalError as e:
            LOGGER.exception(e)
            diagnostics_report.record_failure(e, self)

        except Exception as e:
            LOGGER.exception(e)
            diagnostics_report.record_failure(e, self)
