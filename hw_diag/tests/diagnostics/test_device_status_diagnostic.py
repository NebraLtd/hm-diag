import unittest
from unittest.mock import patch

from hm_pyhelper.diagnostics.diagnostics_report import \
    DIAGNOSTICS_PASSED_KEY, DIAGNOSTICS_ERRORS_KEY, DiagnosticsReport
from hw_diag.diagnostics.device_status_diagnostic import DeviceStatusDiagnostic


class MockBalenaSupervisor:
    def __init__(self, status_return_value) -> None:
        self.status_return_value = status_return_value

    def get_device_status(self, key):
        return self.status_return_value


class TestDeviceStatusDiagnostic(unittest.TestCase):
    @patch(
      "hw_diag.diagnostics.device_status_diagnostic.BalenaSupervisor.new_from_env",
      return_value=MockBalenaSupervisor('applied'))
    def test_success(self, mock):
        diagnostic = DeviceStatusDiagnostic()
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: True,
            DIAGNOSTICS_ERRORS_KEY: [],
            'device_status': 'device_ready'
        })

    @patch(
      "hw_diag.diagnostics.device_status_diagnostic.BalenaSupervisor.new_from_env",
      return_value=MockBalenaSupervisor('applying'))
    def test_failure(self, mock):
        diagnostic = DeviceStatusDiagnostic()
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: False,
            DIAGNOSTICS_ERRORS_KEY: ['device_status', 'device_status'],
            'device_status': 'appState is applying'
        })
