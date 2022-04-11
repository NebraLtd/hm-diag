from hm_pyhelper.diagnostics import DiagnosticsReport
from hw_diag.diagnostics.pgp_signed_json_diagnostic import PgpSignedJsonDiagnostic
from hw_diag.utilities.balena_supervisor import shutdown
from hw_diag.utilities.security import GnuPG

# TODO move to pyhelper constants
SHUTDOWN_GATEWAY_KEY = 'shutdown_gateway'


class ShutdownGatewayDiagnostic(PgpSignedJsonDiagnostic):
    """
    Uses Balena supervisor API to invoke a shutdown on the device if
    SHUTDOWN_GATEWAY_KEY is present in the JSON object embedded in
    the signed PGP.
    """
    # Error message
    NO_SHUTDOWN_GATEWAY_KEY_MSG = "Shutdown gateway key not found in payload JSON."

    def __init__(self, gnupg: GnuPG, shutdown_gateway_with_signature: bytes):
        super(ShutdownGatewayDiagnostic, self).\
            __init__(gnupg, shutdown_gateway_with_signature, SHUTDOWN_GATEWAY_KEY)

    def use_verified_json(self, diagnostics_report: DiagnosticsReport) -> None:
        if SHUTDOWN_GATEWAY_KEY not in self.verified_json:
            diagnostics_report.record_failure(self.NO_SHUTDOWN_GATEWAY_KEY_MSG, self)
            return

        try:
            shutdown_response = shutdown()
            diagnostics_report.record_result(shutdown_response, self)
        except Exception as e:
            diagnostics_report.record_failure(e, self)
