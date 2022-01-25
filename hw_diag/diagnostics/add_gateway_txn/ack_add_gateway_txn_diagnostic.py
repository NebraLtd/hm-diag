from hm_pyhelper.constants.shipping import DESTINATION_WALLETS_KEY
from hw_diag.utilities.hardware import remove_destination_wallets_from_nebra_json
from .base_add_gateway_txn_diagnostic import BaseAddGatewayTxnDiagnostic


class AckAddGatewayTxnDiagnostic(BaseAddGatewayTxnDiagnostic):
    """
    Removes DESTINATION_WALLETS_KEY from Nebra JSON if DESTINATION_NAME_KEY is present.
    Records an error if DESTINATION_WALLETS_KEY is absent.
    """
    def __init__(self):
        super(AckAddGatewayTxnDiagnostic, self). \
            __init__(DESTINATION_WALLETS_KEY, DESTINATION_WALLETS_KEY)

    def remove_destination_wallets(self) -> bool:
        try:
            remove_destination_wallets_from_nebra_json()
            # Intentionally not recording a result, because we want the key to be omitted
            return True
        except Exception as e:
            self.diagnostics_report.record_failure(e, self)
            return False

    def get_steps(self):
        return [
            self.load_and_validate_nebra_json,
            self.load_and_validate_destination_wallets,
            self.remove_destination_wallets,
        ]
