from hm_pyhelper.diagnostics import DiagnosticsReport
from hm_pyhelper.constants.diagnostics import VARIANT_KEY, FREQUENCY_KEY, DISK_IMAGE_KEY
from hm_pyhelper.constants.shipping import DESTINATION_NAME_KEY
from .json_expected_key_diagnostic import JsonExpectedKeyDiagnostic
from hw_diag.utilities.hardware import get_nebra_json


class NebraJsonDiagnostics():
    """
    Copies values from nebra.json file found to a DiagnosticsReport.
    When constructing a new DiagnosticsReport, place NebraJsonDiagnostic after EnvVarDiagnostics
    in order to overwrite values.
    """
    # Destination wallets omitted because it will never be copied to a DiagnosticsReport.
    NEBRA_JSON_EXPECTED_KEYS = [VARIANT_KEY,
                                FREQUENCY_KEY,
                                DISK_IMAGE_KEY,
                                DESTINATION_NAME_KEY]

    def gen_expected_key_diagnostics(self):
        self.nebra_json = get_nebra_json()

        def gen_expected_key_diagnostic(key):
            return JsonExpectedKeyDiagnostic(key, self.nebra_json)

        self.nebra_json_diagnostics = map(gen_expected_key_diagnostic,
                                          self.NEBRA_JSON_EXPECTED_KEYS)

    def perform_expected_key_tests(self, diagnostics_report: DiagnosticsReport):
        for nebra_json_diagnostic in self.nebra_json_diagnostics:
            nebra_json_diagnostic.perform_test(diagnostics_report)

    def perform_test(self, diagnostics_report: DiagnosticsReport):
        self.gen_expected_key_diagnostics()
        self.perform_expected_key_tests(diagnostics_report)
