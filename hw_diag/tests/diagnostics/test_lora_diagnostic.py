import unittest
from unittest.mock import patch

from hm_pyhelper.diagnostics.diagnostics_report import \
    DIAGNOSTICS_PASSED_KEY, DIAGNOSTICS_ERRORS_KEY, DiagnosticsReport
from hw_diag.diagnostics.lora_diagnostic import LoraDiagnostic


class TestLoraDiagnostic(unittest.TestCase):
    @patch(
      "hw_diag.diagnostics.lora_diagnostic.lora_module_test",
      return_value=True)
    def test_success(self, mock):
        diagnostic = LoraDiagnostic()
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: True,
            DIAGNOSTICS_ERRORS_KEY: [],
            'LOR': True,
            'lora': True
        })

    @patch(
      "hw_diag.diagnostics.lora_diagnostic.lora_module_test",
      return_value=False)
    def test_failure(self, mock):
        diagnostic = LoraDiagnostic()
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: False,
            DIAGNOSTICS_ERRORS_KEY: ['LOR'],
            'LOR': False,
            'lora': False
        })
