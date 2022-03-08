from subprocess import CalledProcessError
import unittest
import os
from unittest.mock import MagicMock, patch

from hw_diag.utilities.quectel import ensure_quectel_health, find_eg25g_modem
from hw_diag.utilities.quectel import firmware_upgrade_with_rollback
from hw_diag.utilities.quectel import update_setting_with_rollback, is_att_sim
from hw_diag.utilities.quectel import EG25G_DESIRED_FW
from hw_diag.utilities.dbus_proxy.modem import Modem
from hw_diag.utilities.dbus_proxy.sim import Sim
from hw_diag.utilities.keystore import KeyStore


MOCKED_STATE_FILE = "./tmp_fw_state"
MOCKED_MODEM0_PROPERTIES_GOOD1 = {"Revision": "EG25GGBR07A08M2G"}
MOCKED_MODEM0_PROPERTIES_GOOD2 = {"Revision": "EG25GGBR07A07M2G"}
MOCKED_MODEM0_PROPERTIES_BAD = {"Revision": "EG25GGBR07A07M2H"}


class TestQuectel(unittest.TestCase):
    def setUp(self) -> None:
        if os.path.exists(MOCKED_STATE_FILE):
            os.remove(MOCKED_STATE_FILE)
        return super().setUp()

    def mock_modem(self, mock_object, modem_properties):
        # Make mocked modems
        modem0 = MagicMock()
        mocked_modems = [modem0]

        # Set mocked modems and their properties in dbus
        mocked_object = mock_object.return_value
        mocked_object.GetManagedObjects.return_value = mocked_modems

        mocked_object.GetAll.return_value = modem_properties

    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_find_modem_good(self, mock_interface, _):
        """
        test two known good revisions for eg25g to test modem discovery function
        """
        self.mock_modem(mock_interface, MOCKED_MODEM0_PROPERTIES_GOOD1)
        modem = find_eg25g_modem()
        self.assertIsInstance(modem, Modem)

        self.mock_modem(mock_interface, MOCKED_MODEM0_PROPERTIES_GOOD2)
        modem = find_eg25g_modem()
        self.assertIsInstance(modem, Modem)

    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_find_modem_bad(self, mock_interface, _):
        """
        test that a unsupported modem identifier will result in no modem
        found and failed upgrade.
        """
        self.mock_modem(mock_interface, MOCKED_MODEM0_PROPERTIES_BAD)
        modem = find_eg25g_modem()
        self.assertIsNone(modem)
        self.assertFalse(firmware_upgrade_with_rollback())
        self.assertFalse(update_setting_with_rollback("get_ue_mode", "set_ue_mode", "01"))

    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_sim_identification(self, mock_interface, _):
        """
        Test if SIM identification works correctly.
        """
        self.mock_modem(mock_interface, MOCKED_MODEM0_PROPERTIES_GOOD1)

        # create sim object
        sim = Sim("/org.freedesktop.ModemManager1/Modem/0/Sim/0")
        mock_interface.Get("Sim").return_value = sim

        # first return ATT operator id and then T-Mobile operator id
        with patch(
            "hw_diag.utilities.dbus_proxy.sim.Sim.get_property",
            side_effect=["310280", "310160"],
        ):
            self.assertTrue(is_att_sim())
            self.assertFalse(is_att_sim())

    @patch("hw_diag.utilities.quectel.MODEM_RESET_WAIT_TIME", 0.001)
    @patch("hw_diag.utilities.quectel.INTERNET_MAX_WAIT_TIME", 0.001)
    @patch("hw_diag.utilities.quectel.FW_STATE_FILE", MOCKED_STATE_FILE)
    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    @patch(
        "hw_diag.utilities.dbus_proxy.systemd_unit.SystemDUnit._wait_state",
        return_value=True,
    )
    def test_firmware_upgrade_with_rollback(self, _, mock_interface, _2):
        """
        Test firmware upgrade with rollback function for external process failure
        and rollback due to internet connectivity lost.
        dbus messages about quectel modem are mocked
        reset wait times are mocked to reduce test time, modem is mocked and there is
        no real reset happening
        Firmware_state filename is mocked so that we can independently test it.
        """
        mode_get_property_mock_id = "hw_diag.utilities.dbus_proxy.modem.Modem.get_property"
        self.mock_modem(mock_interface, MOCKED_MODEM0_PROPERTIES_GOOD1)
        # two modems for which we support firmware upgrade and one with revision
        # that we are not aware of.
        with patch("hw_diag.utilities.quectel._do_upgrade", return_value=True):
            with patch(mode_get_property_mock_id, return_value="EG25GGBR07A08M2G"):
                self.assertTrue(firmware_upgrade_with_rollback())
            with patch(mode_get_property_mock_id, return_value="EG25GGBR07A07M2G"):
                self.assertTrue(firmware_upgrade_with_rollback())
            with patch(mode_get_property_mock_id, return_value="unknown"):
                self.assertFalse(firmware_upgrade_with_rollback())

            # internet available before upgrade but lost after that.
            with patch(
                "hw_diag.utilities.quectel.is_internet_accessible",
                side_effect=[True, False],
            ):
                with patch(mode_get_property_mock_id, return_value="EG25GGBR07A07M2G"):
                    self.assertTrue(firmware_upgrade_with_rollback())
                    value = KeyStore(MOCKED_STATE_FILE).get(EG25G_DESIRED_FW["EG25GGBR07A07M2G"], 0)
                    self.assertEqual(value, 1)

        # subprocess failure
        with patch(
            "subprocess.check_output",
            side_effect=CalledProcessError(returncode=1, cmd="QFirehose", output="mocked error"),
        ):
            modem_revision = "EG25GGBR07A08M2G"
            with patch(mode_get_property_mock_id, return_value=modem_revision):
                self.assertFalse(firmware_upgrade_with_rollback())

    @patch("hw_diag.utilities.quectel.ensure_modem_manager_health")
    @patch("hw_diag.utilities.quectel.download_modem_firmware")
    @patch("hw_diag.utilities.quectel.update_setting_with_rollback")
    @patch("hw_diag.utilities.quectel.firmware_upgrade_with_rollback")
    @patch("hw_diag.utilities.quectel.is_att_sim", return_value=True)
    @patch(
        "hw_diag.utilities.quectel.get_firmware_versions",
        return_value=MOCKED_MODEM0_PROPERTIES_GOOD1["Revision"],
    )
    def test_evn_variable(
        self,
        mock_get_firmware_versions,
        mock_is_att_sim,
        mock_firmware_upgrade_with_rollback,
        mock_update_setting_with_rollback,
        mock_download_modem_firmware,
        mock_ensure_modem_manager_health,
    ):
        """
        tests side effects of env variable.
        checks that right functions have been called with right count
        """

        # if control variable is not defined, we should only download the firmware
        ensure_quectel_health()
        self.assertEqual(mock_ensure_modem_manager_health.call_count, 1)
        self.assertEqual(mock_download_modem_firmware.call_count, 1)
        self.assertEqual(mock_update_setting_with_rollback.call_count, 2)
        self.assertEqual(mock_firmware_upgrade_with_rollback.call_count, 0)

        # if quectel is defined, we should run through all the steps
        with patch.dict(os.environ, {"UPDATE_QUECTEL_EG25G_MODEM": "1"}):
            ensure_quectel_health()
            self.assertEqual(mock_ensure_modem_manager_health.call_count, 2)
            self.assertEqual(mock_download_modem_firmware.call_count, 2)
            self.assertEqual(mock_update_setting_with_rollback.call_count, 4)
            self.assertEqual(mock_firmware_upgrade_with_rollback.call_count, 1)
