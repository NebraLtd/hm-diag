import unittest
from unittest.mock import patch, MagicMock
from dbus import DBusException

from hm_pyhelper.diagnostics.diagnostics_report import \
    DIAGNOSTICS_PASSED_KEY, DIAGNOSTICS_ERRORS_KEY, DiagnosticsReport

from hw_diag.diagnostics.lte_diagnostic import LteDiagnostic


class TestLteDiagnostics(unittest.TestCase):

    @patch('dbus.SystemBus')
    @patch('dbus.Interface')
    def test_success(self, mock_interface, mock_sys_bus):
        # Make mocked modems
        modem0 = MagicMock()
        mock_modems = [modem0]

        # Properties of a mocked modem with LTE capability
        mock_modem0_properties = {
            'Model': 'QUECTEL Mobile Broadband Module',
            'Manufacturer': 'QUALCOMM INCORPORATED',
            'CurrentCapabilities': 9,
            'EquipmentIdentifier': '867698048214905',
        }

        # Set mocked modems and their properties in dbus
        mock_interface = mock_interface.return_value
        mock_interface.GetManagedObjects.return_value = mock_modems
        mock_interface.GetAll.return_value = mock_modem0_properties

        diagnostic = LteDiagnostic()
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: True,
            DIAGNOSTICS_ERRORS_KEY: [],
            'LTE': [
                {'EquipmentIdentifier': '867698048214905',
                 'Manufacturer': 'QUALCOMM INCORPORATED',
                 'Model': 'QUECTEL Mobile Broadband Module'}],
            'lte': [
                {'EquipmentIdentifier': '867698048214905',
                 'Manufacturer': 'QUALCOMM INCORPORATED',
                 'Model': 'QUECTEL Mobile Broadband Module'}],
        })

    @patch('dbus.SystemBus')
    @patch('dbus.Interface')
    def test_failure_no_devices(self, mock_interface, mock_sys_bus):
        # Make mocked modems
        mocked_modems = []

        # Set mocked modems in dbus
        mocked_interface = mock_interface.return_value
        mocked_interface.GetManagedObjects.return_value = mocked_modems

        diagnostic = LteDiagnostic()
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: False,
            DIAGNOSTICS_ERRORS_KEY: ['LTE', 'lte'],
            'LTE': 'ModemManager is working but, no LTE devices detected.',
            'lte': 'ModemManager is working but, no LTE devices detected.'
        })

    @patch('dbus.SystemBus')
    @patch('dbus.Interface', side_effect=DBusException('Not authorized'))
    def test_failure_exception(self, mock_interface, mock_sys_bus):
        # Make mocked modems
        mocked_modems = []

        # Set mocked modems in dbus
        mocked_interface = mock_interface.return_value
        mocked_interface.GetManagedObjects.return_value = mocked_modems

        diagnostic = LteDiagnostic()
        diagnostics_report = DiagnosticsReport([diagnostic])
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: False,
            DIAGNOSTICS_ERRORS_KEY: ['LTE', 'lte'],
            'LTE': 'Not authorized',
            'lte': 'Not authorized'
        })
