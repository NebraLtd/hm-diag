import unittest
from unittest.mock import patch

from hm_pyhelper.diagnostics.diagnostics_report import \
    DIAGNOSTICS_PASSED_KEY, DIAGNOSTICS_ERRORS_KEY, DiagnosticsReport
from hw_diag.diagnostics.ecc_diagnostic import EccDiagnostic
from hm_pyhelper.exceptions import ECCMalfunctionException,\
    GatewayMFRFileNotFoundException
from hm_pyhelper.lock_singleton import ResourceBusyError


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
            DIAGNOSTICS_ERRORS_KEY: ['ECC', 'ECC'],
            'ECC': 'gateway_mfr test finished with error, {"result": "fail"}'
        })

    @patch(
        "hw_diag.diagnostics.ecc_diagnostic.get_gateway_mfr_test_result",
        side_effect=ECCMalfunctionException("ECC Malfunctioned"))
    def test_ecc_exception(self, mock):
        diagnostic = EccDiagnostic()
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: False,
            DIAGNOSTICS_ERRORS_KEY: ['ECC', 'ECC'],
            'ECC': 'ECC Malfunctioned'
        })

    @patch(
        "hw_diag.diagnostics.ecc_diagnostic.get_gateway_mfr_test_result",
        side_effect=GatewayMFRFileNotFoundException
        ("Gateway MFR File Not Found"))
    def test_gateway_exception(self, mock):
        diagnostic = EccDiagnostic()
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: False,
            DIAGNOSTICS_ERRORS_KEY: ['ECC', 'ECC'],
            'ECC': 'Gateway MFR File Not Found'
        })

    @patch(
        "hw_diag.diagnostics.ecc_diagnostic.get_gateway_mfr_test_result",
        side_effect=ResourceBusyError("Resource Busy Error"))
    def test_resourcebusy_exception(self, mock):
        diagnostic = EccDiagnostic()
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: False,
            DIAGNOSTICS_ERRORS_KEY: ['ECC', 'ECC'],
            'ECC': 'Resource Busy Error'
        })

    @patch(
        "hw_diag.diagnostics.ecc_diagnostic.get_gateway_mfr_test_result",
        side_effect=UnboundLocalError("Unbound Local Error"))
    def test_unboundlocalerror_exception(self, mock):
        diagnostic = EccDiagnostic()
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: False,
            DIAGNOSTICS_ERRORS_KEY: ['ECC', 'ECC'],
            'ECC': 'Unbound Local Error'
        })
