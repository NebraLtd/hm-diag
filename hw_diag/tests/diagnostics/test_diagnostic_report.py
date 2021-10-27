import unittest

from hw_diag.diagnostics.diagnostic import Diagnostic
from hw_diag.diagnostics.diagnostics_report import \
    DIAGNOSTICS_PASSED_KEY, DIAGNOSTICS_ERRORS_KEY, DiagnosticsReport


class TestDiagnostic(unittest.TestCase):
    def test_record_result(self):
        diagnostic = Diagnostic('key', 'friendly_name')
        diagnostics_report = DiagnosticsReport()
        diagnostics_report.record_result('foo', diagnostic)

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: True,
            DIAGNOSTICS_ERRORS_KEY: [],
            'key': 'foo',
            'friendly_name': 'foo'
        })

    def test_record_failure(self):
        diagnostic = Diagnostic('key', 'friendly_name')
        diagnostics_report = DiagnosticsReport()
        diagnostics_report.record_failure('foo', diagnostic)

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: False,
            DIAGNOSTICS_ERRORS_KEY: ['key'],
            'key': 'foo',
            'friendly_name': 'foo'
        })
