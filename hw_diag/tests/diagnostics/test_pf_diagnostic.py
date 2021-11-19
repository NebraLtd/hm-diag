import unittest

from hm_pyhelper.diagnostics.diagnostics_report import \
    DIAGNOSTICS_PASSED_KEY, DIAGNOSTICS_ERRORS_KEY, DiagnosticsReport
from hw_diag.diagnostics.pf_diagnostic import PfDiagnostic, CHECK_KEYS


class TestPfDiagnostic(unittest.TestCase):
    def test_success(self):
        diagnostic = PfDiagnostic()
        diagnostics_report = DiagnosticsReport([diagnostic])
        for key in CHECK_KEYS:
            diagnostics_report[key] = True
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: True,
            DIAGNOSTICS_ERRORS_KEY: [],
            'PF': True,
            'legacy_pass_fail': True,
            'BT': True,
            'E0': True,
            'LOR': True,
            'ECC': True,
            'PF': True,
        })

    def test_failure(self):
        diagnostic = PfDiagnostic()
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: False,
            DIAGNOSTICS_ERRORS_KEY: ['PF'],
            'PF': False,
            'legacy_pass_fail': False,
        })
