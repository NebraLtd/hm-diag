import unittest
from unittest.mock import patch, mock_open
from hm_pyhelper.diagnostics.diagnostics_report import \
    DIAGNOSTICS_PASSED_KEY, DIAGNOSTICS_ERRORS_KEY, DiagnosticsReport
from hm_pyhelper.constants.diagnostics import ETH_MAC_ADDRESS_KEY, WIFI_MAC_ADDRESS_KEY
from hw_diag.diagnostics.mac_diagnostics import MacDiagnostic, MacDiagnostics


class TestMacDiagnostics(unittest.TestCase):
    @patch("hw_diag.diagnostics.mac_diagnostics.get_mac_address",
           return_value='foo')
    def test_success(self, mock):
        diagnostic = MacDiagnostic('I0', 'friendly', '/')
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: True,
            DIAGNOSTICS_ERRORS_KEY: [],
            'I0': 'foo',
            'friendly': 'foo'
        })

    @patch("hw_diag.diagnostics.mac_diagnostics.get_mac_address",
           new_callable=mock_open)
    def test_error(self, mock):
        mock.side_effect = Exception('No file')
        diagnostic = MacDiagnostic('I0', 'friendly', '/')
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: False,
            DIAGNOSTICS_ERRORS_KEY: ['I0', 'friendly'],
            'I0': 'No file',
            'friendly': 'No file'
        })

    @patch("hw_diag.diagnostics.mac_diagnostics.get_mac_address",
           return_value='foo')
    def test_macs_success(self, mock):
        diagnostic = MacDiagnostics()
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: True,
            DIAGNOSTICS_ERRORS_KEY: [],
            'E0': 'foo',
            'eth_mac_address': 'foo',
            'W0': 'foo',
            'wifi_mac_address': 'foo'
        })

    @patch("hw_diag.diagnostics.mac_diagnostics.get_mac_address",
           side_effect=FileNotFoundError("File Not Found Error"))
    def test_macs_file_exception(self, mock):
        diagnostic = MacDiagnostics()
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: False,
            DIAGNOSTICS_ERRORS_KEY: ['E0', ETH_MAC_ADDRESS_KEY, 'W0', WIFI_MAC_ADDRESS_KEY],
            'E0': 'File Not Found Error',
            'eth_mac_address': 'File Not Found Error',
            'W0': 'File Not Found Error',
            'wifi_mac_address': 'File Not Found Error'
        })

    @patch("hw_diag.diagnostics.mac_diagnostics.get_mac_address",
           side_effect=PermissionError("Permission Error"))
    def test_macs_permission_exception(self, mock):
        diagnostic = MacDiagnostics()
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: False,
            DIAGNOSTICS_ERRORS_KEY: ['E0', ETH_MAC_ADDRESS_KEY, 'W0', WIFI_MAC_ADDRESS_KEY],
            'E0': 'Permission Error',
            'eth_mac_address': 'Permission Error',
            'W0': 'Permission Error',
            'wifi_mac_address': 'Permission Error'
        })
