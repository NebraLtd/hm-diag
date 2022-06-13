import unittest
from unittest.mock import patch

from icmplib import Hop, Host

import hw_diag
from hw_diag.utilities.network_watchdog import NetworkWatchdog


class TestNetworkWatchdog(unittest.TestCase):
    TEST_INTERNAL_NETWORK_IP = '10.16.18.1'     # NOSONAR
    TEST_GATEWAY_IP = '192.168.1.1'             # NOSONAR

    @patch('hw_diag.utilities.network_watchdog.traceroute',
           return_value=[Hop(address=TEST_INTERNAL_NETWORK_IP,
                             packets_sent=2,
                             rtts=[0.4, 0.3],
                             distance=1),
                         Hop(address=TEST_GATEWAY_IP,
                             packets_sent=2,
                             rtts=[0.4, 0.3],
                             distance=2)])
    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_find_gateway_ip_success(self, _, __, ___):
        watchdog = NetworkWatchdog()
        gateway_ip = watchdog.find_gateway_ip()
        self.assertEqual(gateway_ip, self.TEST_GATEWAY_IP)

    @patch('hw_diag.utilities.network_watchdog.traceroute', return_value=[])
    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_find_gateway_ip_fail(self, _, __, ___):
        watchdog = NetworkWatchdog()
        gateway_ip = watchdog.find_gateway_ip()
        self.assertEqual(gateway_ip, '')

    @patch.object(hw_diag.utilities.keystore.KeyStore, 'set')
    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_save_previous_gateway_ip_success(self, _, __, ___):
        watchdog = NetworkWatchdog()
        watchdog.save_previous_gateway_ip(self.TEST_GATEWAY_IP)

    @patch.object(hw_diag.utilities.keystore.KeyStore, 'get', return_value=TEST_GATEWAY_IP)
    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_get_previous_gateway_ip_success(self, _, __, ___):
        watchdog = NetworkWatchdog()
        previous_gateway_ip = watchdog.get_previous_gateway_ip()
        self.assertEqual(previous_gateway_ip, self.TEST_GATEWAY_IP)

    @patch.object(hw_diag.utilities.keystore.KeyStore, 'get', return_value='')
    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_get_previous_gateway_ip_fail(self, _, __, ___):
        watchdog = NetworkWatchdog()
        previous_gateway_ip = watchdog.get_previous_gateway_ip()
        self.assertEqual(previous_gateway_ip, '')

    @patch('hw_diag.utilities.network_watchdog.ping', return_value=Host(address=TEST_GATEWAY_IP,
                                                                        packets_sent=4,
                                                                        rtts=[0.3, 0.4]))
    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_icmp_ping_success(self, _, __, ___):
        watchdog = NetworkWatchdog()
        result = watchdog.icmp_ping(self.TEST_GATEWAY_IP)
        self.assertTrue(result)

    @patch('hw_diag.utilities.network_watchdog.ping', return_value=Host(address=TEST_GATEWAY_IP,
                                                                        packets_sent=0,
                                                                        rtts=[]))
    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_icmp_ping_fail(self, _, __, ___):
        watchdog = NetworkWatchdog()
        result = watchdog.icmp_ping('')
        self.assertFalse(result)

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

    @patch.object(hw_diag.utilities.network_watchdog.NetworkWatchdog, 'icmp_ping',
                  return_value=True)
    @patch.object(hw_diag.utilities.network_watchdog.NetworkWatchdog, 'find_gateway_ip')
    @patch('socket.create_connection')
    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_is_connected(self, _, __, ___, ____, _____):
        watchdog = NetworkWatchdog()
        is_connected = watchdog.is_connected()
        self.assertTrue(is_connected)

    @patch.object(hw_diag.utilities.network_watchdog.NetworkWatchdog, 'icmp_ping',
                  return_value=False)
    @patch.object(hw_diag.utilities.network_watchdog.NetworkWatchdog, 'find_gateway_ip')
    @patch('socket.create_connection')
    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_not_connected(self, _, __, ___, ____, _____):
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

    @patch.object(NetworkWatchdog, 'is_connected', return_value=True)
    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_ensure_network_connection_connected(self, _, __, ___):
        watchdog = NetworkWatchdog()
        with self.assertLogs(level='INFO') as captured_logs:
            watchdog.ensure_network_connection()
            self.assertIn('Ensuring the network connection...', captured_logs.output[0])
            self.assertIn('Network is working.', captured_logs.output[1])

    @patch.object(NetworkWatchdog, 'is_connected', return_value=False)
    @patch.object(hw_diag.utilities.network_watchdog.NetworkWatchdog, 'restart_network_manager')
    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_ensure_network_connection_disconnected(self, _, __, ___, ____):
        watchdog = NetworkWatchdog()
        with self.assertLogs(level='INFO') as captured_logs:
            watchdog.ensure_network_connection()
            self.assertIn('Ensuring the network connection...', captured_logs.output[0])
            self.assertIn(
                'Network is not connected! Lost connectivity count=1', captured_logs.output[1])
