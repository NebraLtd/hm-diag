import unittest
import os
from hm_pyhelper.diagnostics.diagnostics_report import \
    DIAGNOSTICS_PASSED_KEY, DIAGNOSTICS_ERRORS_KEY, DiagnosticsReport

from hw_diag.diagnostics.env_var_diagnostics import \
    EnvVarDiagnostic, EnvVarDiagnostics


class TestEnvVarDiagnostics(unittest.TestCase):
    def test_success(self):
        os.environ['ENV_VAR'] = 'foo'
        diagnostic = EnvVarDiagnostic('DIAGNOSTIC_KEY', 'ENV_VAR')
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: True,
            DIAGNOSTICS_ERRORS_KEY: [],
            'DIAGNOSTIC_KEY': 'foo',
            'ENV_VAR': 'foo'
        })

    def test_error(self):
        os.environ['ENV_VAR'] = ''
        diagnostic = EnvVarDiagnostic('DIAGNOSTIC_KEY', 'ENV_VAR')
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: False,
            DIAGNOSTICS_ERRORS_KEY: ['DIAGNOSTIC_KEY', 'ENV_VAR'],
            'DIAGNOSTIC_KEY': 'Env var ENV_VAR not set',
            'ENV_VAR': 'Env var ENV_VAR not set'
        })

    def test_env_vars_success(self):
        for mapping in EnvVarDiagnostics.ENV_VARS_MAPPING:
            os.environ[mapping['ENV_VAR']] = 'foo'

        diagnostic = EnvVarDiagnostics()
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: True,
            DIAGNOSTICS_ERRORS_KEY: [],
            'BALENA_DEVICE_NAME_AT_INIT': 'foo',
            'BN': 'foo',
            'BALENA_DEVICE_UUID': 'foo',
            'ID': 'foo',
            'BALENA_APP_NAME': 'foo',
            'BA': 'foo',
            'FIRMWARE_VERSION': 'foo',
            'FW': 'foo',
            'VARIANT': 'foo',
            'VA': 'foo',
            # We're moving towards longer lowercase key naming and will
            # deprecate old ones in near future. Just keeping this entry in the
            # list for the sake of style compatibility.
            'FIRMWARE_SHORT_HASH': 'foo',
            'firmware_short_hash': 'foo'
        })
