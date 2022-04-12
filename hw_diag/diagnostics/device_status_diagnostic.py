from hm_pyhelper.diagnostics import DiagnosticsReport
from hm_pyhelper.diagnostics.diagnostic import Diagnostic
from hw_diag.utilities.balena_supervisor import get_device_status


class DeviceStatusDiagnostic(Diagnostic):
    """
    Uses Balena supervisor API to get device status and if status is not "success"
    then the diagnostic is considered to have failed.
    """

    KEY = 'DS'
    FRIENDLY_NAME = "device_status"

    def __init__(self):
        super().__init__(self.KEY, self.FRIENDLY_NAME)

    def perform_test(self, diagnostics_report: DiagnosticsReport) -> None:
        try:
            device_status = get_device_status()
            if device_status['status'] == 'success':
                diagnostics_report.record_result("device_ready", self)
            else:
                diagnostics_report.record_failure(device_status['status'], self)

        except Exception as e:
            diagnostics_report.record_failure(str(e), self)
