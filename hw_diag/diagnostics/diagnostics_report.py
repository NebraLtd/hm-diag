import json

# Name of key in diagnostics containing meta-information about
# the overall state of the miner.
DIAGNOSTICS_PASSED_KEY = 'diagnostics_passed'

# Name of key containing an array of all the diagnostics
# that are considered to be errors.
DIAGNOSTICS_ERRORS_KEY = 'errors'


class DiagnosticsReport(dict):
    def __init__(self, diagnostics=[], **kwargs):
        """
        Intended to be used for constructing a DiagnosticsReport
        manually, or deserializing from JSON.

        When constructing manually, use this format:
            diagnostics = [
                ExampleDiagnostic()
            ]
            diagnostics_report = DiagnosticsReport(diagnostics)

        When deserializing from JSON string:
            report_json_str = '{"diagnostics_passed": false, "errors": ["blah"], "ECC": false}'
            report = DiagnosticsReport.from_json_str(report_json_str)
        """
        super(DiagnosticsReport, self).__init__(kwargs)

        if DIAGNOSTICS_PASSED_KEY not in self:
            self.__setitem__(DIAGNOSTICS_PASSED_KEY, True)

        if DIAGNOSTICS_ERRORS_KEY not in self:
            self.__setitem__(DIAGNOSTICS_ERRORS_KEY, [])
        self.diagnostics = diagnostics

    def passed(self):
        return self[DIAGNOSTICS_PASSED_KEY]

    def set_passed(self, passed):
        self.__setitem__(DIAGNOSTICS_PASSED_KEY, passed)

    def append_error(self, key):
        self.__getitem__(DIAGNOSTICS_ERRORS_KEY).append(key)

    def get_errors(self):
        return self[DIAGNOSTICS_ERRORS_KEY]

    def perform_diagnostics(self):
        for diagnostic in self.diagnostics:
            diagnostic.perform_test(self)

    def record_result(self, result, diagnostic):
        """
        Add the result to both key and friendly name, until key
        is deprecated.
        """
        self.__setitem__(diagnostic.key, result)
        # The current keys are terse. Let's migrate to human friendly ones.
        self.__setitem__(diagnostic.friendly_name, result)

    def record_failure(self, msg_or_exception, diagnostic):
        """
        Set the overall diagnostics status to failure and add this error
        to the list.
        """
        # If one test fails, then the overall state is a failure
        self.set_passed(False)

        # Add the failing key to list of errors
        self.append_error(diagnostic.key)

        # Provide additional details, like error message
        record_failure_as = msg_or_exception
        # Don't stringify bools
        if not isinstance(msg_or_exception, bool):
            record_failure_as = str(record_failure_as)
        self.record_result(record_failure_as, diagnostic)

    def get_report_subset(self, keys_to_extract):
        return {key: self.__getattribute__(key) for key in keys_to_extract}

    @staticmethod
    def from_json_str(json_str):
        report_dict = json.loads(json_str)
        return DiagnosticsReport(**report_dict)
