from hm_pyhelper.diagnostics import DiagnosticsReport
from hm_pyhelper.diagnostics.diagnostic import Diagnostic

from hw_diag.utilities.balena_supervisor import BalenaSupervisor


class DeviceStatusDiagnostic(Diagnostic):
    """
    Uses Balena supervisor API to get device status and if status is not "success"
    then the diagnostic is considered to have failed.
    """

    KEY = 'device_status'
    FRIENDLY_KEY = "device_status"

    def __init__(self):
        super().__init__(self.KEY, self.FRIENDLY_KEY)

    def perform_test(self, diagnostics_report: DiagnosticsReport) -> None:
        try:
            balena_supervisor = BalenaSupervisor.new_from_env()
            device_status = balena_supervisor.get_device_status()

            if device_status == 'success':
                diagnostics_report.record_result("device_ready", self)
            else:
                diagnostics_report.record_failure(device_status, self)

        except Exception as e:
            diagnostics_report.record_failure(str(e), self)
