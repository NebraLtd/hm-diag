import unittest
from unittest.mock import patch
import datetime

from hm_pyhelper.diagnostics.diagnostics_report import \
    DIAGNOSTICS_PASSED_KEY, DIAGNOSTICS_ERRORS_KEY, DiagnosticsReport
from hw_diag.diagnostics.pf_diagnostic import UpdatedAtDiagnostic, CHECK_KEYS

NOW = datetime.datetime(2021, 12, 28, 23, 55, 34, 625194)

class TestUpdatedAtDiagnostic(unittest.TestCase):
    @patch(
      "datetime.datetime.utcnow",
      return_value=NOW)
    def test_success(self):
        diagnostic = UpdatedAtDiagnostic()
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: True,
            DIAGNOSTICS_ERRORS_KEY: [],
            'last_updated': 123,
            'updated_at_unix': 123,
        })

    @patch("datetime.strftime",
           side_effect=ValueError("Bad format"))
    def test_failure(self):
        """
        None of the system calls are ever expected to rais an
        exception, but you never know.
        """
        diagnostic = UpdatedAtDiagnostic()
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: False,
            DIAGNOSTICS_ERRORS_KEY: ['last_updated', 'updated_at_unix'],
            'last_updated': "Bad format",
            'updated_at_unix': "Bad format",
        })
