import json
import re

from hm_pyhelper.diagnostics import DiagnosticsReport
from hm_pyhelper.lock_singleton import ResourceBusyError
from hm_pyhelper.miner_param import LOGGER, get_ecc_location, get_gateway_mfr_test_result
from hm_pyhelper.diagnostics.diagnostic import Diagnostic
from hm_pyhelper.exceptions import ECCMalfunctionException,\
    GatewayMFRFileNotFoundException, UnknownVariantException


class EccDiagnostic(Diagnostic):
    # Diagnostics keys
    KEY = 'ECC'
    FRIENDLY_NAME = "ECC"

    def __init__(self):
        super(EccDiagnostic, self).__init__(self.KEY, self.FRIENDLY_NAME)

    def is_0x58_pass(self, ecc_tests: dict) -> bool:
        """ECCs at 0x58 are expected to fail the `lockable` test.
        If this is really the only test that fails, consider it a pass.
        """

        tests = ecc_tests.get('tests', {})
        fail_count = len([t for t in tests.values() if t['result'] == 'fail'])

        try:
            ecc_location = get_ecc_location()
            m = re.search(r':(\d+)(\?slot=(\d+))?', ecc_location)
            if m:
                groups = m.groups()
                address, slot = (
                    int(groups[0]) if groups[0] is not None else 0x60,
                    int(groups[2]) if groups[2] is not None else 0,
                )
            else:
                address, slot = 0x60, 0
        except UnknownVariantException:
            address, slot = 0x60, 0

        try:
            lockable = tests[f'key_config({slot})']['checks']['lockable'] == 'true'
        except KeyError:
            lockable = False

        return fail_count == 1 and lockable is False and address == 0x58

    def perform_test(self, diagnostics_report: DiagnosticsReport) -> None:
        try:
            ecc_tests = get_gateway_mfr_test_result()

            if ecc_tests['result'] == 'pass':
                diagnostics_report.record_result(True, self)
            else:
                if self.is_0x58_pass(ecc_tests):
                    LOGGER.info("Ignoring wrong lockable flag on 0x58 ECC")
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
