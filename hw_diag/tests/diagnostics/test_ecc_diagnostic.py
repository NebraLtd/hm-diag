import unittest
from unittest.mock import patch

from hm_pyhelper.diagnostics.diagnostics_report import \
    DIAGNOSTICS_PASSED_KEY, DIAGNOSTICS_ERRORS_KEY, DiagnosticsReport
from hw_diag.diagnostics.ecc_diagnostic import EccDiagnostic
from hm_pyhelper.exceptions import ECCMalfunctionException


class TestECCDiagnostic(unittest.TestCase):
    @patch(
      "hw_diag.diagnostics.ecc_diagnostic.get_gateway_mfr_test_result",
      return_value={'result': 'pass'})
    def test_success(self, mock):
        diagnostic = EccDiagnostic()
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: True,
            DIAGNOSTICS_ERRORS_KEY: [],
            'ECC': True
        })

    @patch(
      "hw_diag.diagnostics.ecc_diagnostic.get_gateway_mfr_test_result",
      return_value={'result': 'fail'})
    def test_failure(self, mock):
        diagnostic = EccDiagnostic()
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: False,
            DIAGNOSTICS_ERRORS_KEY: ['ECC'],
            'ECC': 'gateway_mfr test finished with error, {"result": "fail"}'
        })

    @patch(
        "hw_diag.diagnostics.ecc_diagnostic.get_gateway_mfr_test_result",
        side_effect=ECCMalfunctionException("ECC Malfunctioned"))
    def test_exception(self, mock):
        diagnostic = EccDiagnostic()
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: False,
            DIAGNOSTICS_ERRORS_KEY: ['ECC'],
            'ECC': 'ECC Malfunctioned'
        })
