import datetime
import unittest
from unittest.mock import patch

import hw_diag
from hw_diag.utilities.network_watchdog import NetworkWatchdog


class TestNetworkWatchdog(unittest.TestCase):

    @patch('socket.create_connection')
    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_have_internet(self, _, __, ___):
        watchdog = NetworkWatchdog()
        have_internet = watchdog.have_internet()
        self.assertTrue(have_internet)

    @patch('socket.create_connection', side_effect=TimeoutError())
    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_no_internet(self, _, __, ___):
        watchdog = NetworkWatchdog()
        have_internet = watchdog.have_internet()
        self.assertFalse(have_internet)

    @patch.object(hw_diag.utilities.dbus_proxy.network_manager.NetworkManager, 'is_connected',
                  return_value=True)
    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_is_connected(self, _, __, ___):
        watchdog = NetworkWatchdog()
        is_connected = watchdog.is_connected()
        self.assertTrue(is_connected)

    @patch.object(hw_diag.utilities.dbus_proxy.network_manager.NetworkManager, 'is_connected',
                  return_value=False)
    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_not_connected(self, _, __, ___):
        watchdog = NetworkWatchdog()
        is_connected = watchdog.is_connected()
        self.assertFalse(is_connected)

    @patch.object(hw_diag.utilities.dbus_proxy.systemd_unit.SystemDUnit, 'wait_restart')
    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_restart_network_manager_success(self, _, __, ___):
        watchdog = NetworkWatchdog()
        with self.assertLogs(level='INFO') as captured_logs:
            watchdog.restart_network_manager()
            self.assertIn('Network manager restarted:', captured_logs.output[0])

    @patch.object(hw_diag.utilities.keystore.KeyStore, 'get', return_value='01/06/2022 08:24:14')
    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_get_last_restart_success(self, _, __, ___):
        watchdog = NetworkWatchdog()
        last_restart = watchdog.get_last_restart()
        expected = datetime.datetime(2022, 6, 1, 8, 24, 14)
        self.assertEqual(last_restart, expected)

    @patch.object(hw_diag.utilities.keystore.KeyStore, 'get', return_value='')
    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_get_last_restart_invalid_input(self, _, __, ___):
        watchdog = NetworkWatchdog()
        last_restart = watchdog.get_last_restart()
        expected = datetime.datetime.min
        self.assertEqual(last_restart, expected)

    @patch.object(hw_diag.utilities.keystore.KeyStore, 'set')
    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_save_last_restart_success(self, _, __, ___):
        watchdog = NetworkWatchdog()
        with self.assertLogs(level='INFO') as captured_logs:
            watchdog.save_last_restart()
            self.assertIn('Saved the current time before restarting the hotpsot.',
                          captured_logs.output[0])

    @patch.object(hw_diag.utilities.keystore.KeyStore, 'set', side_effect=FileNotFoundError())
    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_save_last_restart_fail(self, _, __, ___):
        watchdog = NetworkWatchdog()
        with self.assertRaises(FileNotFoundError):
            watchdog.save_last_restart()

    @patch.object(NetworkWatchdog, 'is_connected', return_value=True)
    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_run_watchdog_connected(self, _, __, ___):
        watchdog = NetworkWatchdog()
        with self.assertLogs(level='INFO') as captured_logs:
            watchdog.run_watchdog()
            self.assertIn('INFO:hw_diag.utilities.network_watchdog:Running the watchdog...',
                          captured_logs.output)
            self.assertIn('INFO:hw_diag.utilities.network_watchdog:Network is working.',
                          captured_logs.output)

    @patch.object(NetworkWatchdog, 'is_connected', return_value=False)
    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_run_watchdog_disconnected(self, _, __, ___):
        watchdog = NetworkWatchdog()
        with self.assertLogs(level='INFO') as captured_logs:
            watchdog.run_watchdog()
            self.assertIn('Running the watchdog...', captured_logs.output[0])
            self.assertIn(
                'Network is not connected! Lost connectivity count=1', captured_logs.output[1])
