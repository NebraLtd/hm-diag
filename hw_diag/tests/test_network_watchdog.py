import unittest
from unittest.mock import patch

import hw_diag
from hw_diag.utilities.network_watchdog import NetworkWatchdog


class TestNetworkWatchdog(unittest.TestCase):

    @patch('socket.create_connection')
    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_have_internet(self, _, __, ___):
        watchdog = NetworkWatchdog.get_instance()
        have_internet = watchdog.have_internet()
        self.assertTrue(have_internet)

    @patch('socket.create_connection', side_effect=TimeoutError())
    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_no_internet(self, _, __, ___):
        watchdog = NetworkWatchdog.get_instance()
        have_internet = watchdog.have_internet()
        self.assertFalse(have_internet)

    @patch('socket.create_connection')
    @patch.object(hw_diag.utilities.dbus_proxy.network_manager.NetworkManager, 'is_connected',
                  return_value=True)
    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_is_connected(self, _, __, ___, ____):
        watchdog = NetworkWatchdog.get_instance()
        is_connected = watchdog.is_connected()
        self.assertTrue(is_connected)

    @patch.object(hw_diag.utilities.dbus_proxy.network_manager.NetworkManager, 'is_connected',
                  return_value=False)
    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_not_connected(self, _, __, ___):
        watchdog = NetworkWatchdog.get_instance()
        is_connected = watchdog.is_connected()
        self.assertFalse(is_connected)

    @patch.object(hw_diag.utilities.dbus_proxy.systemd_unit.SystemDUnit, 'wait_restart')
    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_restart_network_manager_success(self, _, __, ___):
        watchdog = NetworkWatchdog.get_instance()
        with self.assertLogs(level='INFO') as captured_logs:
            watchdog.restart_network_manager()
            self.assertIn('Network manager restarted:', captured_logs.output[0])

    @patch.object(NetworkWatchdog, 'is_connected', return_value=True)
    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_run_watchdog_connected(self, _, __, ___):
        watchdog = NetworkWatchdog.get_instance()
        with self.assertLogs(level='INFO') as captured_logs:
            watchdog.ensure_network_connection()
            self.assertIn('INFO:hw_diag.utilities.network_watchdog:Running the watchdog...',
                          captured_logs.output)
            self.assertIn('INFO:hw_diag.utilities.network_watchdog:Network is working.',
                          captured_logs.output)

    @patch.object(NetworkWatchdog, 'is_connected', return_value=False)
    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_run_watchdog_disconnected(self, _, __, ___):
        watchdog = NetworkWatchdog.get_instance()
        with self.assertLogs(level='INFO') as captured_logs:
            watchdog.ensure_network_connection()
            self.assertIn('Running the watchdog...', captured_logs.output[0])
            self.assertIn(
                'Network is not connected! Lost connectivity count=1', captured_logs.output[1])
