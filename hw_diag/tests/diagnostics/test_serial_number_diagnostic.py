import unittest
from unittest.mock import patch, mock_open

from hm_pyhelper.diagnostics.diagnostics_report import \
    DIAGNOSTICS_PASSED_KEY, DIAGNOSTICS_ERRORS_KEY, DiagnosticsReport
from hw_diag.diagnostics.serial_number_diagnostic import SerialNumberDiagnostic

VALID_CPU_PROC = """00000000ddd1a4c2"""
PADDED_CPU_PROC = "%s\x00" % VALID_CPU_PROC


class TestSerialNumberDiagnostic(unittest.TestCase):

    @patch("builtins.open", new_callable=mock_open, read_data=VALID_CPU_PROC)
    def test_success(self, mock):
        diagnostic = SerialNumberDiagnostic()
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: True,
            DIAGNOSTICS_ERRORS_KEY: [],
            'serial_number': '00000000ddd1a4c2',
            'serial_number': '00000000ddd1a4c2'
        })

    @patch("builtins.open", new_callable=mock_open, read_data=PADDED_CPU_PROC)
    def test_success_strip(self, mock):
        diagnostic = SerialNumberDiagnostic()
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: True,
            DIAGNOSTICS_ERRORS_KEY: [],
            'serial_number': '00000000ddd1a4c2',
            'serial_number': '00000000ddd1a4c2'
        })

    @patch("builtins.open", new_callable=mock_open)
    def test_filenotfound(self, mock):
        mock.side_effect = FileNotFoundError("File not found")
        diagnostic = SerialNumberDiagnostic()
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: False,
            DIAGNOSTICS_ERRORS_KEY: ['serial_number'],
            'serial_number': 'File not found',
            'serial_number': 'File not found'
        })

    @patch("builtins.open", new_callable=mock_open)
    def test_permissionerror(self, mock):
        mock.side_effect = PermissionError("Bad permissions")
        diagnostic = SerialNumberDiagnostic()
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: False,
            DIAGNOSTICS_ERRORS_KEY: ['serial_number'],
            'serial_number': 'Bad permissions',
            'serial_number': 'Bad permissions'
        })
