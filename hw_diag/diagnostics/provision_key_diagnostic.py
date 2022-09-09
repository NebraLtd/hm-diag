from hm_pyhelper.diagnostics import DiagnosticsReport
from hm_pyhelper.miner_param import provision_key

from hw_diag.diagnostics.pgp_signed_json_diagnostic import PgpSignedJsonDiagnostic
from hw_diag.utilities.balena_supervisor import BalenaSupervisor
from hw_diag.utilities.security import GnuPG

KEY_PROVISIONING_KEY = 'provision_key'


class ProvisionKeyDiagnostic(PgpSignedJsonDiagnostic):
    """
    Uses Balena supervisor API to invoke a shutdown on the device if
    SHUTDOWN_GATEWAY_KEY is present in the JSON object embedded in
    the signed PGP.
    """

    def __init__(self, gnupg: GnuPG, provision_request_with_signature: bytes):
        super(ProvisionKeyDiagnostic, self).\
            __init__(gnupg, provision_request_with_signature, KEY_PROVISIONING_KEY)

    def use_verified_json(self, diagnostics_report: DiagnosticsReport) -> None:
        if 'slot' not in self.verified_json or 'force' not in self.verified_json:
            diagnostics_report.record_failure("Invalid payload, missing keys")
            return None

        slot = self.verified_json['slot']
        force = self.verified_json['force']

        success, result = provision_key(slot=slot, force=force)
        if success:
            diagnostics_report.record_result(result, self)
        else:
            diagnostics_report.record_failure(result, self)
