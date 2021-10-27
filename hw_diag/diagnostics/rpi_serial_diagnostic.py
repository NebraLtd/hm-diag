
from hm_pyhelper.diagnostics.diagnostic import Diagnostic

KEY = 'RPI'
FRIENDLY_NAME = "raspberry_pi_serial_number"
SERIAL_FILEPATH = "/proc/cpuinfo"


class RpiSerialDiagnostic(Diagnostic):
    def __init__(self):
        super(RpiSerialDiagnostic, self). \
            __init__(KEY, FRIENDLY_NAME)

    def perform_test(self, diagnostics_report):
        try:
            rpi_serial = open(SERIAL_FILEPATH).readlines()[-2].strip()[10:]
            diagnostics_report.record_result(rpi_serial, self)

        except FileNotFoundError as e:
            diagnostics_report.record_failure(e, self)

        except PermissionError as e:
            diagnostics_report.record_failure(e, self)
