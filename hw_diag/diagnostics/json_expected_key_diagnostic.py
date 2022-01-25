from hm_pyhelper.diagnostics import Diagnostic, DiagnosticsReport


class JsonExpectedKeyDiagnostic(Diagnostic):
    """
    Record result if `key` is present and not empty in `nebra_json`.
    """
    def __init__(self, key, json_dict: dict):
        super(JsonExpectedKeyDiagnostic, self).__init__(key, key)
        self.json_dict = json_dict

    def perform_test(self, diagnostics_report: DiagnosticsReport):
        if self.json_dict is None:
            diagnostics_report.record_failure("JSON is empty.", self)
            return

        if self.key in self.json_dict:
            json_val = self.json_dict[self.key]

            if len(json_val) > 0:
                # Key is present and not empty
                diagnostics_report.record_result(json_val, self)
                return
            else:
                # Key is present but empty
                diagnostics_report.record_failure(f"The value for key \"{self.key}\" "
                                                  "in JSON is empty.", self)
                return
        else:
            # Missing key
            diagnostics_report.record_failure(f"JSON file does not contain key \"{self.key}\".",
                                              self)
            return
