import unittest
import os
from unittest.mock import MagicMock, patch

from hw_diag.utilities.quectel import find_eg25g_modem, firmware_upgrade_with_rollback
from hw_diag.utilities.quectel import update_setting_with_rollback
from hw_diag.utilities.dbus_proxy.modem import Modem

FW_STATE_FILE = '/tmp/fw_state'


class TestQuectel(unittest.TestCase):

    def setUp(self) -> None:
        if os.path.exists(FW_STATE_FILE):
            os.remove(FW_STATE_FILE)
        return super().setUp()

    @patch('dbus.SystemBus')
    @patch('dbus.Interface')
    def test_find_modem(self, mock_interface, _):
        # Make mocked modems
        modem0 = MagicMock()
        mocked_modems = [modem0]

        # Set mocked modems and their properties in dbus
        mocked_interface = mock_interface.return_value
        mocked_interface.GetManagedObjects.return_value = mocked_modems

        # various revision for mocked modem, two known good for eg25g and one unknown
        mocked_modem0_properties_good1 = {'Revision': 'EG25GGBR07A08M2G'}
        mocked_modem0_properties_good2 = {'Revision': 'EG25GGBR07A07M2G'}
        mocked_modem0_properties_bad = {'Revision': 'EG25GGBR07A07M2H'}

        mocked_interface.GetAll.return_value = mocked_modem0_properties_good1
        modem = find_eg25g_modem()
        self.assertIsInstance(modem, Modem)

        mocked_interface.GetAll.return_value = mocked_modem0_properties_good2
        modem = find_eg25g_modem()
        self.assertIsInstance(modem, Modem)

        mocked_interface.GetAll.return_value = mocked_modem0_properties_bad
        modem = find_eg25g_modem()
        self.assertIsNone(modem)
        self.assertFalse(firmware_upgrade_with_rollback())
        self.assertFalse(update_setting_with_rollback('get_ue_mode', 'set_ue_mode', '01'))
