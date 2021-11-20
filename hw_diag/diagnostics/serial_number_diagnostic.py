
from hm_pyhelper.diagnostics.diagnostic import Diagnostic

KEY = 'serial_number'
FRIENDLY_NAME = "serial_number"
SERIAL_FILEPATH = "/proc/device-tree/serial-number"


class SerialNumberDiagnostic(Diagnostic):
    def __init__(self):
        super(SerialNumberDiagnostic, self). \
            __init__(KEY, FRIENDLY_NAME)

    def perform_test(self, diagnostics_report):
        try:
            serial_number = open(SERIAL_FILEPATH).readline()
            diagnostics_report.record_result(serial_number, self)

        except FileNotFoundError as e:
            diagnostics_report.record_failure(e, self)

        except PermissionError as e:
            diagnostics_report.record_failure(e, self)
