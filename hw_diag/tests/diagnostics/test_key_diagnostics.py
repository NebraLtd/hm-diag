import unittest
from unittest.mock import patch

from hm_pyhelper.diagnostics.diagnostics_report import \
    DIAGNOSTICS_PASSED_KEY, DIAGNOSTICS_ERRORS_KEY, DiagnosticsReport
from hw_diag.diagnostics.key_diagnostics import KeyDiagnostic, KeyDiagnostics


class TestKeyDiagnostics(unittest.TestCase):
    @patch(
      "hw_diag.diagnostics.key_diagnostics.get_public_keys_rust",
      return_value={'key_location': '123'})
    def test_success(self, mock):
        diagnostic = KeyDiagnostic('KK', 'test_key', 'key_location')
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: True,
            DIAGNOSTICS_ERRORS_KEY: [],
            'KK': '123',
            'test_key': '123'
        })

    @patch(
      "hw_diag.diagnostics.key_diagnostics.get_public_keys_rust",
      return_value={'different_location': '123'})
    def test_failure(self, mock):
        diagnostic = KeyDiagnostic('KK', 'test_key', 'key_location')
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: False,
            DIAGNOSTICS_ERRORS_KEY: ['KK'],
            'KK': 'Key key_location not found',
            'test_key': 'Key key_location not found'
        })

    @patch(
      "hw_diag.diagnostics.key_diagnostics.get_public_keys_rust",
      return_value={'key': '123'})
    def test_keys_success(self, mock):
        diagnostic = KeyDiagnostics()
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: True,
            DIAGNOSTICS_ERRORS_KEY: [],
            'PK': '123',
            'public_key': '123',
            'OK': '123',
            'onboarding_key': '123'
        })
