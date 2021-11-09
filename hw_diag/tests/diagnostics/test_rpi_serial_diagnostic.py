import unittest
from unittest.mock import patch, mock_open

from hm_pyhelper.diagnostics.diagnostics_report import \
    DIAGNOSTICS_PASSED_KEY, DIAGNOSTICS_ERRORS_KEY, DiagnosticsReport
from hw_diag.diagnostics.rpi_serial_diagnostic import RpiSerialDiagnostic

VALID_CPU_PROC = """Hardware	: BCM2835
Revision	: a02100
Serial		: 00000000ddd1a4c2
Model		: Raspberry Pi Compute Module 3 Plus Rev 1.0
"""


class TestRpiSerialDiagnostic(unittest.TestCase):

    @patch("builtins.open", new_callable=mock_open, read_data=VALID_CPU_PROC)
    def test_success(self, mock):
        diagnostic = RpiSerialDiagnostic()
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: True,
            DIAGNOSTICS_ERRORS_KEY: [],
            'RPI': '00000000ddd1a4c2',
            'raspberry_pi_serial_number': '00000000ddd1a4c2'
        })

    @patch("builtins.open", new_callable=mock_open)
    def test_filenotfound(self, mock):
        mock.side_effect = FileNotFoundError("File not found")
        diagnostic = RpiSerialDiagnostic()
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: False,
            DIAGNOSTICS_ERRORS_KEY: ['RPI'],
            'RPI': 'File not found',
            'raspberry_pi_serial_number': 'File not found'
        })

    @patch("builtins.open", new_callable=mock_open)
    def test_permissionerror(self, mock):
        mock.side_effect = PermissionError("Bad permissions")
        diagnostic = RpiSerialDiagnostic()
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: False,
            DIAGNOSTICS_ERRORS_KEY: ['RPI'],
            'RPI': 'Bad permissions',
            'raspberry_pi_serial_number': 'Bad permissions'
        })
