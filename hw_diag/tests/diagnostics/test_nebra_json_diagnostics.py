import unittest
from unittest.mock import patch

from hm_pyhelper.diagnostics.diagnostics_report import \
    DIAGNOSTICS_PASSED_KEY, DIAGNOSTICS_ERRORS_KEY, DiagnosticsReport
from hm_pyhelper.constants.diagnostics import VARIANT_KEY, FREQUENCY_KEY, DISK_IMAGE_KEY
from hm_pyhelper.constants.shipping import DESTINATION_NAME_KEY
from hw_diag.diagnostics.nebra_json_diagnostics import NebraJsonDiagnostics


class TestNebraJsonDiagnostics(unittest.TestCase):
    NEBRA_JSON_SUCCESS = {
        VARIANT_KEY: 'variant',
        FREQUENCY_KEY: 'frequency',
        DISK_IMAGE_KEY: 'disk_image',
        DESTINATION_NAME_KEY: 'destination_name'
    }

    @patch("hw_diag.diagnostics.nebra_json_diagnostics.get_nebra_json",
           return_value=NEBRA_JSON_SUCCESS)
    def test_success(self, get_nebra_json_mock):
        diagnostic = NebraJsonDiagnostics()
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: True,
            DIAGNOSTICS_ERRORS_KEY: [],
            VARIANT_KEY: 'variant',
            FREQUENCY_KEY: 'frequency',
            DISK_IMAGE_KEY: 'disk_image',
            DESTINATION_NAME_KEY: 'destination_name'
        })

    @patch("hw_diag.diagnostics.nebra_json_diagnostics.get_nebra_json",
           return_value=None)
    def test_invalid_file(self, get_nebra_json_mock):
        diagnostic = NebraJsonDiagnostics()
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: False,
            DIAGNOSTICS_ERRORS_KEY: [VARIANT_KEY, VARIANT_KEY, FREQUENCY_KEY, FREQUENCY_KEY,
                                     DISK_IMAGE_KEY, DISK_IMAGE_KEY,
                                     DESTINATION_NAME_KEY, DESTINATION_NAME_KEY],
            VARIANT_KEY: 'JSON is empty.',
            FREQUENCY_KEY: 'JSON is empty.',
            DISK_IMAGE_KEY: 'JSON is empty.',
            DESTINATION_NAME_KEY: 'JSON is empty.'
        })
