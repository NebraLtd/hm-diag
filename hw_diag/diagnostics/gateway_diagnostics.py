from hm_pyhelper.diagnostics import DiagnosticsReport
from hm_pyhelper.diagnostics.diagnostic import Diagnostic
from hm_pyhelper.gateway_grpc.client import GatewayClient, decode_pub_key
from hm_pyhelper.miner_param import LOGGER
import grpc


class GatwayGRPCMethodCallMixin:
    def call_grpc_and_record_status(self, diagnostics_report: DiagnosticsReport,
                                    method_name: str, *args,
                                    **kwargs) -> object:
        """
        Call a method on the gateway grpc client amd record failures if any.
        Recording success is caller's responsibility.
        :param method_name: The method name to call.
        :param args: The arguments to pass to the method.
        :param kwargs: The keyword arguments to pass to the method.
        :return: The result of the method call.
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


class DiagnosticKeyInfo:
    def __init__(self, friendly_key: str, key: str = None):
        self.friendly_key = friendly_key
        if key is None:
            self.key = friendly_key
        else:
            self.key = key


class ValidatorDiagnostic(Diagnostic, GatwayGRPCMethodCallMixin):
    SUPPORTED_VALIDATOR_ATTRIBUTES = [
        DiagnosticKeyInfo('validator_address'),
        DiagnosticKeyInfo('validator_uri'),
        DiagnosticKeyInfo('block_age'),
        DiagnosticKeyInfo('validator_height', 'MH')
    ]

    def __init__(self, key: str, friendly_name: str):
        super(ValidatorDiagnostic, self).__init__(key, friendly_name)

    def perform_test(self, diagnostics_report):
        validator_info = self.call_grpc_and_record_status(diagnostics_report, "get_validator_info")
        if not validator_info:
            return

        if self.friendly_key == 'validator_address':
            diagnostics_report.record_result(
                decode_pub_key(validator_info.gateway.address), self)
        elif self.friendly_key == 'validator_uri':
            diagnostics_report.record_result(validator_info.gateway.uri, self)
        elif self.friendly_key == 'block_age':
            diagnostics_report.record_result(validator_info.block_age, self)
        elif self.friendly_key == 'validator_height':
            diagnostics_report.record_result(validator_info.height, self)
        else:
            diagnostics_report.record_failure(
                f"{self.friendly_key} is not a validator property", self)


class RegionDiagnostic(Diagnostic, GatwayGRPCMethodCallMixin):
    KEY = 'RE'
    FRIENDLY_NAME = 'miner_region'

    def __init__(self):
        super(RegionDiagnostic, self).__init__(self.KEY, self.FRIENDLY_NAME)

    def perform_test(self, diagnostics_report):
        region = self.call_grpc_and_record_status(diagnostics_report, "get_region")
        if region:
            diagnostics_report.record_result(region, self)


class MinerPubKeyDiagnostic(Diagnostic, GatwayGRPCMethodCallMixin):
    FRIENDLY_NAME = 'miner_pubkey'
    KEY = FRIENDLY_NAME

    def __init__(self):
        super(MinerPubKeyDiagnostic, self).__init__(self.KEY, self.FRIENDLY_NAME)

    def perform_test(self, diagnostics_report):
        miner_pubkey = self.call_grpc_and_record_status(diagnostics_report, "get_pubkey")
        if miner_pubkey:
            diagnostics_report.record_result(miner_pubkey, self)


class GatewayDiagnostics(Diagnostic):
    def __init__(self):
        self.gateway_diagnostics = [
            RegionDiagnostic(),
            MinerPubKeyDiagnostic(),
        ]
        for attribute in ValidatorDiagnostic.SUPPORTED_VALIDATOR_ATTRIBUTES:
            self.gateway_diagnostics.append(
                ValidatorDiagnostic(attribute.key, attribute.friendly_key))

    def perform_test(self, diagnostics_report: DiagnosticsReport) -> None:
        for diagnostic in self.gateway_diagnostics:
            diagnostic.perform_test(diagnostics_report)
