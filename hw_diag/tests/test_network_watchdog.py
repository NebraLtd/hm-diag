import unittest
from unittest.mock import patch
from icmplib import Host
from hw_diag.utilities.dbus_proxy.network_manager import NetworkManager
from hw_diag.utilities.dbus_proxy.systemd_unit import SystemDUnit
from hw_diag.utilities.event_streamer import DiagEvent
from hw_diag.utilities.network_watchdog import NetworkWatchdog


class TestNetworkWatchdog(unittest.TestCase):
    TEST_GATEWAY_IP = '192.168.1.1'             # NOSONAR

    @patch('hw_diag.utilities.network_watchdog.ping', return_value=Host(address=TEST_GATEWAY_IP,
                                                                        packets_sent=4,
                                                                        rtts=[0.3, 0.4]))
    def test_icmp_ping_success(self, _):
        watchdog = NetworkWatchdog()
        result = watchdog.is_ping_reachable(self.TEST_GATEWAY_IP)
        self.assertTrue(result)

    @patch('hw_diag.utilities.network_watchdog.ping', return_value=Host(address=TEST_GATEWAY_IP,
                                                                        packets_sent=0,
                                                                        rtts=[]))
    def test_icmp_ping_fail(self, _):
        watchdog = NetworkWatchdog()
        result = watchdog.is_ping_reachable('')
        self.assertFalse(result)

    @patch.object(NetworkWatchdog, 'is_ping_reachable', return_value=True)
    @patch.object(NetworkManager, 'get_gateways', return_value=[TEST_GATEWAY_IP])
    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_local_network_connection_success(self, _, __, ___, ____):
        watchdog = NetworkWatchdog()
        is_local_network_connected = watchdog.is_local_network_connected()
        self.assertTrue(is_local_network_connected)
        network_state_event = watchdog.get_current_network_state()
        self.assertEqual(network_state_event, DiagEvent.NETWORK_INTERNET_CONNECTED)

    @patch.object(NetworkWatchdog, 'is_ping_reachable', return_value=False)
    @patch.object(NetworkManager, 'get_gateways', return_value=[TEST_GATEWAY_IP])
    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_local_network_connection_fail(self, _, __, ___, ____):
        watchdog = NetworkWatchdog()
        is_local_network_connected = watchdog.is_local_network_connected()
        self.assertFalse(is_local_network_connected)
        network_state_event = watchdog.get_current_network_state()
        self.assertEqual(network_state_event, DiagEvent.NETWORK_DISCONNECTED)

    @patch.object(NetworkWatchdog, 'is_ping_reachable', return_value=True)
    @patch.object(NetworkManager, 'get_gateways', return_value=[TEST_GATEWAY_IP])
    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_internet_connection_success(self, _, __, ___, ____):
        watchdog = NetworkWatchdog()
        is_internet_connected = watchdog.is_internet_connected()
        self.assertTrue(is_internet_connected)
        network_state_event = watchdog.get_current_network_state()
        self.assertEqual(network_state_event, DiagEvent.NETWORK_INTERNET_CONNECTED)

    @patch.object(NetworkWatchdog, 'is_ping_reachable', return_value=False)
    @patch.object(NetworkManager, 'get_gateways', return_value=[TEST_GATEWAY_IP])
    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_internet_connection_fail(self, _, __, ___, ____):
        watchdog = NetworkWatchdog()
        is_internet_connected = watchdog.is_internet_connected()
        self.assertFalse(is_internet_connected)
        network_state_event = watchdog.get_current_network_state()
        self.assertEqual(network_state_event, DiagEvent.NETWORK_DISCONNECTED)

    @patch.object(NetworkWatchdog, 'is_local_network_connected', return_value=True)
    @patch.object(NetworkWatchdog, 'is_internet_connected', return_value=True)
    def test_connection_success(self, _, __):
        watchdog = NetworkWatchdog()
        is_connected = watchdog.is_connected()
        self.assertTrue(is_connected)
        network_state_event = watchdog.get_current_network_state()
        self.assertEqual(network_state_event, DiagEvent.NETWORK_INTERNET_CONNECTED)

    @patch.object(NetworkWatchdog, 'is_local_network_connected', return_value=False)
    @patch.object(NetworkWatchdog, 'is_internet_connected', return_value=False)
    def test_connection_fail(self, _, __):
        watchdog = NetworkWatchdog()
        is_connected = watchdog.is_connected()
        self.assertFalse(is_connected)
        network_state_event = watchdog.get_current_network_state()
        self.assertEqual(network_state_event, DiagEvent.NETWORK_DISCONNECTED)

    @patch.object(SystemDUnit, 'wait_restart')
    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_restart_network_manager_success(self, _, __, ___):
        watchdog = NetworkWatchdog()
        with self.assertLogs(level='INFO') as captured_logs:
            watchdog.restart_network_manager()
            self.assertIn('Network manager restarted:', captured_logs.output[0])

    @patch.object(NetworkWatchdog, 'is_local_network_connected', return_value=True)
    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_ensure_network_connection_connected(self, _, __, ___):
        watchdog = NetworkWatchdog()
        with self.assertLogs(level='INFO') as captured_logs:
            watchdog.ensure_network_connection()
            self.assertIn('Ensuring the network connection...', captured_logs.output[0])
            self.assertIn('OS has been up for', captured_logs.output[1])
            self.assertIn('Network is working.', captured_logs.output[2])

    @patch.object(NetworkWatchdog, 'is_connected', return_value=False)
    @patch.object(NetworkWatchdog, 'restart_network_manager')
    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_ensure_network_connection_disconnected(self, _, __, ___, ____):
        watchdog = NetworkWatchdog()
        with self.assertLogs(level='INFO') as captured_logs:
            watchdog.ensure_network_connection()
            self.assertIn('Ensuring the network connection...', captured_logs.output[0])
            self.assertIn('OS has been up for', captured_logs.output[1])
            self.assertIn(
                'Network is not connected! Lost connectivity count=1', captured_logs.output[2])
