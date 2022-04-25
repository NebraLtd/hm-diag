from hm_pyhelper.diagnostics import DiagnosticsReport
from hm_pyhelper.diagnostics.diagnostic import Diagnostic
from hw_diag.utilities.miner import fetch_miner_data
from hm_pyhelper.miner_param import LOGGER
import grpc


class GatewayDiagnostic(Diagnostic):
    FRIENDLY_NAME = "gatewayrs"
    KEY = FRIENDLY_NAME

    def __init__(self):
        super(GatewayDiagnostic, self).__init__(self.KEY, self.FRIENDLY_NAME)

    def perform_test(self, diagnostics_report: DiagnosticsReport) -> None:
        diagnostics = {}
        try:
            miner_data = fetch_miner_data(diagnostics)
        except grpc.RpcError as err:
            LOGGER.error(f"rpc error: {err}")
            LOGGER.exception(err)
            diagnostics_report.record_failure(err, self)
        except Exception as err:
            LOGGER.exception(err)
            diagnostics_report.record_failure(err, self)
        diagnostics_report.record_result(diagnostics, self)
