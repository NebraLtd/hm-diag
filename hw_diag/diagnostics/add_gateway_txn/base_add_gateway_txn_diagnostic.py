from hm_pyhelper.diagnostics import Diagnostic, DiagnosticsReport
from hm_pyhelper.constants.shipping import DESTINATION_NAME_KEY, DESTINATION_WALLETS_KEY
from hw_diag.utilities.hardware import get_nebra_json


class BaseAddGatewayTxnDiagnostic(Diagnostic):

    def __init__(self, key, friendly_key):
        super(BaseAddGatewayTxnDiagnostic, self).__init__(key, friendly_key)

    def load_and_validate_nebra_json(self) -> bool:
        """
        Load nebra.json file and record failure if file could not be opened.
        Returns True if file opens successfully.
        """
        self.nebra_json = get_nebra_json()

        if self.nebra_json is None:
            msg = "Nebra JSON could not be loaded or is empty."
            self.diagnostics_report.record_failure(msg, self)
            return False
        else:
            return True

    def load_and_validate_destination_wallets(self) -> bool:
        """
        1. Ensure a destination name is set.
        2. Validate presence of destination wallets.
        3. Ensure destination wallets is not empty or None.

        Record failure and return False if conditions above not met, return True otherwise.
        """

        if DESTINATION_NAME_KEY not in self.nebra_json:
            msg = "Destination name not found in Nebra JSON."
            self.diagnostics_report.record_failure(msg, self)
            return False
        if DESTINATION_WALLETS_KEY not in self.nebra_json:
            # Check that destination wallets are present
            msg = "Destination wallets not found in Nebra JSON."
            self.diagnostics_report.record_failure(msg, self)
            return False
        else:
            self.destination_wallets = self.nebra_json[DESTINATION_WALLETS_KEY]
            # Check if destination wallets contains at least one valid address
            if self.destination_wallets is None or \
               len(self.destination_wallets) == 0:
                msg = "Destination wallets array is empty in Nebra JSON."
                self.diagnostics_report.record_failure(msg, self)
                return False
            return True

    def get_steps(self) -> list:
        """
        For extending classes to implement. Must return an array of methods to
        be executed in order. Each method is responsible for returning True if
        successful. It should return False and invoke DiagnosticsReport#record_failure
        in the case of failure.
        """
        return []

    def perform_test(self, diagnostics_report: DiagnosticsReport):
        """
        Iterate through all steps. Exit immediately if an error is encountered.

        """
        self.diagnostics_report = diagnostics_report

        steps = self.get_steps()
        try:
            for step in steps:
                if not step():
                    return

        except Exception as e:
            self.diagnostics_report.record_failure(e, self)
