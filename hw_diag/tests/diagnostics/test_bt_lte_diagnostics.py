import unittest
from unittest.mock import patch

from hm_pyhelper.diagnostics.diagnostics_report import \
    DIAGNOSTICS_PASSED_KEY, DIAGNOSTICS_ERRORS_KEY, DiagnosticsReport

from hw_diag.diagnostics.bt_lte_diagnostic import \
    BtLteDiagnostic, BtLteDiagnostics


class TestBtLteDiagnostics(unittest.TestCase):
    @patch('os.popen')
    def test_success(self, mock):
        mock().read.return_value = 'dev_addr'
        diagnostic = BtLteDiagnostic('DEV_TYPE', 'dev_addr')
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: True,
            DIAGNOSTICS_ERRORS_KEY: [],
            'DEV_TYPE': True
        })

    @patch('os.popen')
    def test_error(self, mock):
        mock().read.return_value = 'INVALID'
        diagnostic = BtLteDiagnostic('DEV_TYPE', 'dev_addr')
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: True,
            DIAGNOSTICS_ERRORS_KEY: [],
            'DEV_TYPE': False
        })

    @patch('os.popen')
    def test_all_success(self, mock):
        mock().read.return_value = '0a12, 2c7c, 68a2, 1bc7, 1e0e, 12d1, 2cd2'

        diagnostic = BtLteDiagnostics()
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: True,
            DIAGNOSTICS_ERRORS_KEY: [],
            'BT': True,
            'LTE': True,
        })
