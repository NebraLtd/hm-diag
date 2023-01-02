import unittest
from unittest.mock import patch

import responses

from hm_pyhelper.diagnostics.diagnostics_report import \
    DIAGNOSTICS_PASSED_KEY, DIAGNOSTICS_ERRORS_KEY, DiagnosticsReport

from hw_diag.diagnostics.device_status_diagnostic import DeviceStatusDiagnostic
from hw_diag.utilities import balena_supervisor


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

    @responses.activate
    @patch.dict(
        balena_supervisor.os.environ,
        {
          'BALENA_SUPERVISOR_ADDRESS': 'http://127.0.0.1',
          'BALENA_SUPERVISOR_API_KEY': 'secret'
        },
        clear=True
    )
    def test_empty_response(self):
        responses.add(
            responses.GET,
            'http://127.0.0.1/v2/state/status?apikey=secret',
            body='',
            status=200
        )

        diagnostic = DeviceStatusDiagnostic()
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: False,
            DIAGNOSTICS_ERRORS_KEY: ['device_status', 'device_status'],
            'device_status': "Supervisor API did not return valid json response.\n"
                             "Response content: b''"
        })
