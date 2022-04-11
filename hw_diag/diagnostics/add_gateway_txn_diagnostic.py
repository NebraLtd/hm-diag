import secrets

from hm_pyhelper.diagnostics import DiagnosticsReport
from hm_pyhelper.constants.shipping import DESTINATION_WALLETS_KEY, DESTINATION_ADD_GATEWAY_TXN_KEY
from hw_diag.diagnostics.pgp_signed_json_diagnostic import PgpSignedJsonDiagnostic
from hw_diag.utilities.miner import create_add_gateway_txn
from hw_diag.utilities.security import GnuPG


class AddGatewayTxnDiagnostic(PgpSignedJsonDiagnostic):
    # Error message
    NO_DESTINATION_WALLETS_MSG = "Destination wallets not found in payload JSON."

    def __init__(self, gnupg: GnuPG, shipping_destination_with_signature: bytes):
        super(AddGatewayTxnDiagnostic, self).\
            __init__(gnupg, shipping_destination_with_signature, DESTINATION_ADD_GATEWAY_TXN_KEY)

    def use_verified_json(self, diagnostics_report: DiagnosticsReport) -> None:
        if DESTINATION_WALLETS_KEY not in self.verified_json:
            diagnostics_report.record_failure(self.NO_DESTINATION_WALLETS_MSG, self)
            return

        destination_wallet = secrets.choice(self.verified_json[DESTINATION_WALLETS_KEY])

        try:
            add_gateway_txn = create_add_gateway_txn(destination_wallet)
            diagnostics_report.record_result(add_gateway_txn, self)
        except Exception as e:
            diagnostics_report.record_failure(e, self)
