import os
from hm_pyhelper.diagnostics.diagnostic import Diagnostic

ENV_VARS_MAPPING = [{
    'ENV_VAR': 'BALENA_DEVICE_NAME_AT_INIT',
    'DIAGNOSTIC_KEY': 'BN'
}, {
    'ENV_VAR': 'BALENA_DEVICE_UUID',
    'DIAGNOSTIC_KEY': 'ID'
}, {
    'ENV_VAR': 'BALENA_APP_NAME',
    'DIAGNOSTIC_KEY': 'BA'
}, {
    'ENV_VAR': 'FREQ',
    'DIAGNOSTIC_KEY': 'FR'
}, {
    'ENV_VAR': 'FIRMWARE_VERSION',
    'DIAGNOSTIC_KEY': 'FW'
}, {
    'ENV_VAR': 'VARIANT',
    'DIAGNOSTIC_KEY': 'VA'
}, {
    'ENV_VAR': 'FIRMWARE_SHORT_HASH',
    'DIAGNOSTIC_KEY': 'firmware_short_hash'
}]


class EnvVarDiagnostic(Diagnostic):
    def __init__(self, key, friendly_key):
        super(EnvVarDiagnostic, self).__init__(key, friendly_key)

    def perform_test(self, diagnostics_report):
        env_value = os.getenv(self.friendly_key)
        if not env_value:
            diagnostics_report.record_failure(
                "Env var %s not set" % self.friendly_key, self)
        else:
            diagnostics_report.record_result(env_value, self)


class EnvVarDiagnostics():
    def __init__(self):
        def get_diagnostic_for_env_var(env_var_mapping):
            return EnvVarDiagnostic(env_var_mapping['DIAGNOSTIC_KEY'],
                                    env_var_mapping['ENV_VAR'])

        self.env_var_diagnostics = map(get_diagnostic_for_env_var,
                                       ENV_VARS_MAPPING)

    def perform_test(self, diagnostics_report):
        for env_var_diagnostic in self.env_var_diagnostics:
            env_var_diagnostic.perform_test(diagnostics_report)
