from hm_pyhelper.diagnostics import DiagnosticsReport
from hm_pyhelper.diagnostics.diagnostic import Diagnostic
from hm_pyhelper.gateway_grpc.client import GatewayClient, decode_pub_key
from hm_pyhelper.miner_param import LOGGER
from hm_pyhelper.constants import diagnostics as DIAG_CONSTS
import grpc


class DiagnosticKeyInfo:
    def __init__(self, friendly_name: str, short_key: str = None,
                 grpc_method_name: str = None,
                 composed_attribute_path: str = None):
        """"
        Represents a Gateway Diagnostic key required to fetch
        corresponding value.
        composed_attribute_path represents the path inside the value returned
        by grpc call represented by grpc_method_name
        if short_key is not supplied it defaults to friendly_name
        """
        self.friendly_name = friendly_name
        self.short_key = short_key
        if short_key is None:
            self.short_key = friendly_name
        self.grpc_method_name = grpc_method_name
        self.composed_attribute_path = composed_attribute_path


class GatewayDiagnostic(Diagnostic):
    def __init__(self, keyinfo: DiagnosticKeyInfo):
        super(GatewayDiagnostic, self).__init__(keyinfo.short_key, keyinfo.friendly_name)
        self.keyinfo = keyinfo

    def call_grpc(self, diagnostics_report: DiagnosticsReport,
                  method_name: str, *args, **kwargs) -> object:
        """
        returns grpc return value if successful, None otherwise
        """
        try:
            with GatewayClient() as client:
                return getattr(client, method_name)(*args, **kwargs)
        except grpc.RpcError as err:
            LOGGER.error(f"rpc error: {err}")
            LOGGER.exception(err)
            diagnostics_report.record_failure(err, self)
        except Exception as err:
            LOGGER.exception(err)
            diagnostics_report.record_failure(err, self)
        return None

    def perform_test(self, diagnostics_report):
        ret_value = self.call_grpc(diagnostics_report,
                                   self.keyinfo.grpc_method_name)

        # if grpc has failed
        if not ret_value:
            return

        # return simple value
        if not self.keyinfo.composed_attribute_path:
            diagnostics_report.record_result(ret_value, self)
            return

        # flatten the composite value
        try:
            for attribute_name in self.keyinfo.composed_attribute_path.split('.'):
                ret_value = getattr(ret_value, attribute_name)
            # this key requires additional decoding
            if self.keyinfo.friendly_name == DIAG_CONSTS.VALIDATOR_ADDRESS_KEY:
                ret_value = decode_pub_key(ret_value)
            diagnostics_report.record_result(ret_value, self)
        except Exception as err:
            diagnostics_report.record_failure(err, self)


class GatewayDiagnostics(Diagnostic):

    SUPPORTED_GATEWAY_ATTRIBUTES = [
        DiagnosticKeyInfo(friendly_name=DIAG_CONSTS.GATEWAY_PUBKEY_KEY,
                          grpc_method_name='get_pubkey'),
        DiagnosticKeyInfo(friendly_name=DIAG_CONSTS.GATEWAY_REGION_KEY,
                          short_key=DIAG_CONSTS.GATEWAY_REGION_SHORT_KEY,
                          grpc_method_name='get_region'),
    ]

    def __init__(self):
        self.gateway_diagnostics = []
        for attribute in self.SUPPORTED_GATEWAY_ATTRIBUTES:
            self.gateway_diagnostics.append(GatewayDiagnostic(attribute))

    def perform_test(self, diagnostics_report: DiagnosticsReport) -> None:
        for diagnostic in self.gateway_diagnostics:
            diagnostic.perform_test(diagnostics_report)
