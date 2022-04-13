from hm_pyhelper.diagnostics import Diagnostic, DiagnosticsReport
from hw_diag.utilities.security import GnuPG


class PgpSignedJsonDiagnostic(Diagnostic):
    """
    Base class for extracting JSON from a signed PGP payload and conducting
    further processing. Extending classes must implement use_verified_json.
    """

    # Error message
    VERIFICATION_FAILED_MSG = "Verifying the payload PGP signature failed."

    def __init__(self, gnupg: GnuPG, json_with_signature: bytes, diagnostic_key: str):
        super(PgpSignedJsonDiagnostic, self).__init__(diagnostic_key, diagnostic_key)
        self.gnupg = gnupg
        self.json_with_signature = json_with_signature

    def perform_test(self, diagnostics_report: DiagnosticsReport) -> None:
        """
        Verify json_with_signature is signed by valid key and extract JSON.
        Record failure if signature cannot be verified.
        """
        self.verified_json = self.gnupg.get_verified_json(self.json_with_signature)

        if not self.verified_json:
            diagnostics_report.record_failure(self.VERIFICATION_FAILED_MSG, self)
            return

        self.use_verified_json(diagnostics_report)

    def use_verified_json(self, diagnostics_report: DiagnosticsReport):
        """
        To be implemented by extending classes. self.record_result should be
        called as a result of successful invocation or self.record_failure
        in the case of failure.
        """
        raise Exception("use_verified_json must be implemented by extending class.")
