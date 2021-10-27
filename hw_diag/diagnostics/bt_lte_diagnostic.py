import os
from hm_pyhelper.diagnostics.diagnostic import Diagnostic


DEVICE_TYPE_ADDRESS_MAPPINGS = [
    {
        'dev_type': 'BT',
        'dev_addr': '0a12'
    },
    {
        'dev_type': 'LTE',  # Quectel
        'dev_addr': '2c7c'
    },
    {
        'dev_type': 'LTE',  # Sierra Wireless MC7700
        'dev_addr': '68a2'
    },
    {
        'dev_type': 'LTE',  # Telit / Reyax
        'dev_addr': '1bc7'
    },
    {
        'dev_type': 'LTE',  # SimCom SIM7100E
        'dev_addr': '1e0e'
    },
    {
        'dev_type': 'LTE',  # Huawei ME909s-120
        'dev_addr': '12d1'
    },
    {
        'dev_type': 'LTE',  # MikroTik R11e-LTE6
        'dev_addr': '2cd2'
    }
]


class BtLteDiagnostic(Diagnostic):
    def __init__(self, dev_type, dev_addr):
        super(BtLteDiagnostic, self).__init__(dev_type, dev_type)
        self.dev_addr = dev_addr

    def perform_test(self, diagnostics_report):
        resp = os.popen(
            'grep %s /sys/bus/usb/devices/*/idVendor' % self.dev_addr
        ).read()

        if self.dev_addr in resp:
            print("setting %s to %s" % (self.key, True))
            diagnostics_report.record_result(True, self)
        else:
            # Only set the dev_type to False if it is not already true
            if self.key not in diagnostics_report:
                diagnostics_report.record_result(False, self)

            dev_type_already_true = diagnostics_report[self.key]
            if not dev_type_already_true:
                diagnostics_report.record_result(False, self)


class BtLteDiagnostics():
    def __init__(self):
        def get_diagnostic_for_dev(bt_lte_mapping):
            return BtLteDiagnostic(bt_lte_mapping['dev_type'],
                                   bt_lte_mapping['dev_addr'])

        self.bt_lte_diagnostics = map(get_diagnostic_for_dev,
                                      DEVICE_TYPE_ADDRESS_MAPPINGS)

    def perform_test(self, diagnostics_report):
        for bt_lte_diagnostic in self.bt_lte_diagnostics:
            bt_lte_diagnostic.perform_test(diagnostics_report)
