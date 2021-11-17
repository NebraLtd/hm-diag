from hm_pyhelper.exceptions import ECCMalfunctionException
from hm_pyhelper.lock_singleton import ResourceBusyError
from hm_pyhelper.miner_param import get_public_keys_rust
from hm_pyhelper.diagnostics.diagnostic import Diagnostic

KEY_MAPPINGS = [
    {
        'key': 'OK',
        'friendly_key': 'onboarding_key',
        'key_path': 'key'
    },
    {
        'key': 'PK',
        'friendly_key': 'public_key',
        'key_path': 'key'
    }
]


class KeyDiagnostic(Diagnostic):
    def __init__(self, key, friendly_key, key_path):
        super(KeyDiagnostic, self).__init__(key, friendly_key)
        self.key_path = key_path

    def perform_test(self, diagnostics_report):
        # Try to get key, but there may be ECC lock or other failure
        try:
            public_keys = get_public_keys_rust()
        except ECCMalfunctionException as e:
            diagnostics_report.record_failure(e, self)
            return
        except UnboundLocalError as e:
            diagnostics_report.record_failure(e, self)
            return
        except (FileNotFoundError, NotADirectoryError) as e:
            diagnostics_report.record_failure(e, self)
            return
        except ResourceBusyError as e:
            diagnostics_report.record_failure(e, self)
            return
        except Exception as e:
            diagnostics_report.record_failure(e, self)
            return

        # Record key value, or report failure if unable to parse
        try:
            diagnostics_report.record_result(public_keys[self.key_path], self)
        except KeyError:
            err_msg = "Key %s not found" % self.key_path
            diagnostics_report.record_failure(err_msg, self)


class KeyDiagnostics:
    def __init__(self):
        def get_diagnostic_for_key(key_mapping):
            return KeyDiagnostic(
              key_mapping['key'],
              key_mapping['friendly_key'],
              key_mapping['key_path'])

        self.key_diagnostics = map(get_diagnostic_for_key,
                                   KEY_MAPPINGS)

    def perform_test(self, diagnostics_report):
        for key_diagnostic in self.key_diagnostics:
            key_diagnostic.perform_test(diagnostics_report)
