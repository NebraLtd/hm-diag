import unittest
from unittest.mock import patch
from dbus import DBusException

from hm_pyhelper.diagnostics.diagnostics_report import \
    DIAGNOSTICS_PASSED_KEY, DIAGNOSTICS_ERRORS_KEY, DiagnosticsReport

from hw_diag.diagnostics.bt_diagnostic import BtDiagnostic


class TestBtDiagnostic(unittest.TestCase):

    @patch('dbus.SystemBus')
    @patch('dbus.Interface')
    def test_success(self, mock_interface, mock_sys_bus):
        # Prepare mocked BT devices
        mock_bt_devices = {
            '/org/bluez/hci0': {
                'org.bluez.Adapter1': {
                    'Address': '00:E0:4C:19:D2:91',
                    'AddressType': 'public',
                    'Name': 'ble0',
                    'Alias': 'ble0',
                    'Class': '1835268',
                    'Powered': '1',
                    'Discoverable': '1',
                    'DiscoverableTimeout': 0,
                    'Pairable': '1',
                    'PairableTimeout': 0,
                    'Discovering': '0',
                    'UUIDs': [],
                    'Modalias': 'usb:v1D6Bp0246d0535'
                }
            }
        }

        # Mock BT devices in dbus
        mock_interface = mock_interface.return_value
        mock_interface.GetManagedObjects.return_value = mock_bt_devices

        diagnostic = BtDiagnostic()
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: True,
            DIAGNOSTICS_ERRORS_KEY: [],
            'BT': [
                {'Address': '00:E0:4C:19:D2:91',
                    'Discoverable': '1',
                    'Discovering': '0',
                    'Name': 'ble0',
                    'Pairable': '1',
                    'Powered': '1'}
            ],
            'bluetooth': [
                {'Address': '00:E0:4C:19:D2:91',
                    'Discoverable': '1',
                    'Discovering': '0',
                    'Name': 'ble0',
                    'Pairable': '1',
                    'Powered': '1'}]
        })

    @patch('dbus.SystemBus')
    @patch('dbus.Interface')
    def test_failure_no_devices(self, mock_interface, mock_sys_bus):
        # Prepare mocked BT devices
        mock_bt_devices = {}

        # Mock BT devices in dbus
        mock_interface = mock_interface.return_value
        mock_interface.GetManagedObjects.return_value = mock_bt_devices

        diagnostic = BtDiagnostic()
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: False,
            DIAGNOSTICS_ERRORS_KEY: ['BT'],
            'BT': 'Bluez is working but, no Bluetooth devices detected.',
            'bluetooth': 'Bluez is working but, no Bluetooth devices detected.'
        })

    @patch('dbus.SystemBus')
    @patch('dbus.Interface', side_effect=DBusException('Not authorized'))
    def test_failure_exception(self, mock_interface, mock_sys_bus):
        # Prepare mocked BT devices
        mock_bt_devices = {}

        # Mock BT devices in dbus
        mock_interface = mock_interface.return_value
        mock_interface.GetManagedObjects.return_value = mock_bt_devices

        diagnostic = BtDiagnostic()
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: False,
            DIAGNOSTICS_ERRORS_KEY: ['BT'],
            'BT': 'Not authorized',
            'bluetooth': 'Not authorized'
        })
