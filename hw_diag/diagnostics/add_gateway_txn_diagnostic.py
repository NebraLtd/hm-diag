import secrets

from hm_pyhelper.diagnostics import Diagnostic, DiagnosticsReport
from hm_pyhelper.constants.shipping import DESTINATION_WALLETS_KEY, DESTINATION_ADD_GATEWAY_TXN_KEY
from hw_diag.utilities.miner import create_add_gateway_txn
from hw_diag.utilities.security import GnuPG


class AddGatewayTxnDiagnostic(Diagnostic):
    # Error messages
    NO_DESTINATION_WALLETS_MSG = "Destination wallets not found in payload JSON."
    VERIFICATION_FAILED_MSG = "Verifying the payload signature failed."

    def __init__(self, gnupg: GnuPG, shipping_destination_with_signature: bytes):
        super(AddGatewayTxnDiagnostic, self).\
            __init__(DESTINATION_ADD_GATEWAY_TXN_KEY, DESTINATION_ADD_GATEWAY_TXN_KEY)
        self.gnupg = gnupg
        self.shipping_destination_with_signature = shipping_destination_with_signature

    def perform_test(self, diagnostics_report: DiagnosticsReport) -> None:
        shipping_destination_json = self.gnupg.get_verified_json(
            self.shipping_destination_with_signature)

        if not shipping_destination_json:
            diagnostics_report.record_failure(self.VERIFICATION_FAILED_MSG, self)
            return

        if DESTINATION_WALLETS_KEY not in shipping_destination_json:
            diagnostics_report.record_failure(self.NO_DESTINATION_WALLETS_MSG, self)
            return

        destination_wallet = secrets.choice(shipping_destination_json[DESTINATION_WALLETS_KEY])

        try:
            add_gateway_txn = create_add_gateway_txn(destination_wallet)
            diagnostics_report.record_result(add_gateway_txn, self)
        except Exception as e:
            diagnostics_report.record_failure(e, self)
