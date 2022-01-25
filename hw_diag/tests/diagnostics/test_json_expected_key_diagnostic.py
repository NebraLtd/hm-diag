import unittest

from hm_pyhelper.diagnostics.diagnostics_report import \
    DIAGNOSTICS_PASSED_KEY, DIAGNOSTICS_ERRORS_KEY, DiagnosticsReport
from hw_diag.diagnostics.json_expected_key_diagnostic import JsonExpectedKeyDiagnostic


class TestJsonExpectedKeyDiagnostic(unittest.TestCase):
    def test_success(self):
        json_dict = {'foo': 'bar'}
        diagnostic = JsonExpectedKeyDiagnostic('foo', json_dict)
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: True,
            DIAGNOSTICS_ERRORS_KEY: [],
            'foo': 'bar'
        })

    def test_json_none(self):
        json_dict = None
        diagnostic = JsonExpectedKeyDiagnostic('foo', json_dict)
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: False,
            DIAGNOSTICS_ERRORS_KEY: ['foo', 'foo'],
            'foo': 'JSON is empty.'
        })

    def test_missing_key(self):
        json_dict = {'foo': 'bar'}
        diagnostic = JsonExpectedKeyDiagnostic('missing', json_dict)
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: False,
            DIAGNOSTICS_ERRORS_KEY: ['missing', 'missing'],
            'missing': 'JSON file does not contain key "missing".'
        })

    def test_empty_key(self):
        json_dict = {'foo': ''}
        diagnostic = JsonExpectedKeyDiagnostic('foo', json_dict)
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: False,
            DIAGNOSTICS_ERRORS_KEY: ['foo', 'foo'],
            'foo': 'The value for key "foo" in JSON is empty.'
        })
