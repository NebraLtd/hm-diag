from hm_pyhelper.diagnostics import DiagnosticsReport
from hm_pyhelper.miner_param import get_mac_address
from hm_pyhelper.diagnostics.diagnostic import Diagnostic


class MacDiagnostic(Diagnostic):
    def __init__(self, key: str, friendly_key: str, mac_filepath: str):
        super(MacDiagnostic, self).__init__(key, friendly_key)
        self.mac_filepath = mac_filepath

    def perform_test(self, diagnostics_report: DiagnosticsReport) -> None:
        try:
            mac_address = get_mac_address(self.mac_filepath)
            diagnostics_report.record_result(mac_address, self)
        except Exception as e:
            diagnostics_report.record_failure(str(e), self)


class MacDiagnostics():
    INTERFACE_MAPPINGS = [
        {
            'key': 'E0',
            'friendly_key': 'eth_mac_address',
            'mac_filepath': '/sys/class/net/eth0/address'
        },
        {
            'key': 'W0',
            'friendly_key': 'wifi_mac_address',
            'mac_filepath': '/sys/class/net/wlan0/address'
        }
    ]

    def __init__(self):
        def get_diagnostic_for_interface(interface_info: dict) -> Diagnostic:
            return MacDiagnostic(
              interface_info['key'],
              interface_info['friendly_key'],
              interface_info['mac_filepath'])

        self.mac_diagnostics = map(get_diagnostic_for_interface, self.INTERFACE_MAPPINGS)

    def perform_test(self, diagnostics_report: DiagnosticsReport) -> None:
        for mac_diagnostic in self.mac_diagnostics:
            mac_diagnostic.perform_test(diagnostics_report)
