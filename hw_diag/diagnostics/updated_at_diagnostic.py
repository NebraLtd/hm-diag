
import datetime
from hm_pyhelper.diagnostics.diagnostic import Diagnostic

KEY = 'last_updated'
FRIENDLY_NAME = "updated_at_unix"


class UpdatedAtDiagnostic(Diagnostic):
    """
    Sets a new value for last_updated every time
    #perform_test is called.
    """

    def __init__(self):
        super(UpdatedAtDiagnostic, self).__init__(KEY, FRIENDLY_NAME)

    def perform_test(self, diagnostics_report):
        try:
            now = datetime.datetime.utcnow()
            diagnostics['last_updated'] = now.strftime("%H:%M UTC %d %b %Y")

                   diagnostics_report.record_result(True, self)
        else:
            diagnostics_report.record_failure(False, self)