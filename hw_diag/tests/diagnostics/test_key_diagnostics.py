import unittest
from unittest.mock import patch

from hm_pyhelper.diagnostics.diagnostics_report import \
    DIAGNOSTICS_PASSED_KEY, DIAGNOSTICS_ERRORS_KEY, DiagnosticsReport
from hm_pyhelper.exceptions import ECCMalfunctionException
from hm_pyhelper.lock_singleton import ResourceBusyError
import pytest
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
            DIAGNOSTICS_ERRORS_KEY: ['KK', 'test_key'],
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

    @patch(
      "hw_diag.diagnostics.key_diagnostics.KeyDiagnostic.perform_test",
      side_effect=FileNotFoundError("File Not Found Error"))
    def test_filenotfound_exception(self, mock):
        with pytest.raises(FileNotFoundError):
            diagnostic = KeyDiagnostics()
            diagnostics_report = DiagnosticsReport([diagnostic])
            diagnostics_report.perform_diagnostics()

            self.assertDictEqual(diagnostics_report, {
                DIAGNOSTICS_PASSED_KEY: False,
                DIAGNOSTICS_ERRORS_KEY: [],
                'KK': 'File Not Found Error',
            })

    @patch(
      "hw_diag.diagnostics.key_diagnostics.KeyDiagnostic.perform_test",
      side_effect=UnboundLocalError("Unbound Local Error"))
    def test_unboundlocal_exception(self, mock):
        with pytest.raises(UnboundLocalError):
            diagnostic = KeyDiagnostics()
            diagnostics_report = DiagnosticsReport([diagnostic])
            diagnostics_report.perform_diagnostics()

            self.assertDictEqual(diagnostics_report, {
                DIAGNOSTICS_PASSED_KEY: False,
                DIAGNOSTICS_ERRORS_KEY: [],
                'KK': 'Unbound Local Error',
            })

    @patch(
      "hw_diag.diagnostics.key_diagnostics.KeyDiagnostic.perform_test",
      side_effect=ECCMalfunctionException("ECC Malfunction Error"))
    def test_eccmalfunction_exception(self, mock):
        with pytest.raises(ECCMalfunctionException):
            diagnostic = KeyDiagnostics()
            diagnostics_report = DiagnosticsReport([diagnostic])
            diagnostics_report.perform_diagnostics()

            self.assertDictEqual(diagnostics_report, {
                DIAGNOSTICS_PASSED_KEY: False,
                DIAGNOSTICS_ERRORS_KEY: [],
                'KK': 'ECC Malfunction Error',
            })

    @patch(
      "hw_diag.diagnostics.key_diagnostics.KeyDiagnostic.perform_test",
      side_effect=ResourceBusyError("Resource Busy Error"))
    def test_resourcebusy_exception(self, mock):
        with pytest.raises(ResourceBusyError):
            diagnostic = KeyDiagnostics()
            diagnostics_report = DiagnosticsReport([diagnostic])
            diagnostics_report.perform_diagnostics()

            self.assertDictEqual(diagnostics_report, {
                DIAGNOSTICS_PASSED_KEY: False,
                DIAGNOSTICS_ERRORS_KEY: [],
                'KK': 'Resource Busy Error',
            })
