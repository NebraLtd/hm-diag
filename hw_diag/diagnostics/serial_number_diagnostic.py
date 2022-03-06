from hm_pyhelper.diagnostics import DiagnosticsReport
from hm_pyhelper.diagnostics.diagnostic import Diagnostic


class SerialNumberDiagnostic(Diagnostic):
    # Diagnostics keys
    KEY = 'serial_number'
    FRIENDLY_NAME = "serial_number"

    SERIAL_FILEPATH = "/proc/device-tree/serial-number"

    def __init__(self):
        super(SerialNumberDiagnostic, self).__init__(self.KEY, self.FRIENDLY_NAME)

    def perform_test(self, diagnostics_report: DiagnosticsReport) -> None:
        try:
            serial_number = open(self.SERIAL_FILEPATH).readline().rstrip('\x00')
            diagnostics_report.record_result(serial_number, self)

        except FileNotFoundError as e:
            diagnostics_report.record_failure(e, self)

        except PermissionError as e:
            diagnostics_report.record_failure(e, self)
