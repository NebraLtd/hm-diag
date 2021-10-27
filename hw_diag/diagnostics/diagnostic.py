
class Diagnostic():
    def __init__(self, key, friendly_name):
        """
        key - Key of relevant value in diagnostics_report dictionary
        friendly_name - Same as key but a human_friendly_snake_case
                        version. To replace key eventually.
        diagnostics_report - Key value pairs corresponding to
                             diagnostic readings.
        """
        self.key = key
        self.friendly_name = friendly_name

    def perform_test(self, diagnostics_report):
        raise Exception("Should be implemented by extending class")
