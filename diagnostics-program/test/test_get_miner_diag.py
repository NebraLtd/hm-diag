import unittest
from collections import namedtuple
import dbus
from unittest.mock import patch
import sys
sys.path.append("..")
from main import get_miner_diagnostics # noqa


class TestGetMinerDiag(unittest.TestCase):
    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_right_response(self, _, null):
        dbus.SystemBus.return_value = namedtuple(
            "miner_bus",
            "get_object")(get_object=lambda x, y: [])
        dbus.Interface.return_value = namedtuple(
            "miner_interface",
            "P2PStatus")(P2PStatus=lambda: [
                [1, 2, 3, 4],
                [5, 6, 7, 8],
                [9, 10, 11, 12],
                [13, 14, 15, 16],
                [17, 18, 19, 20]
            ])
        res = get_miner_diagnostics()
        self.assertEqual(res, ['2', '10', '20', '14', '6'])

    @patch("dbus.SystemBus")
    @patch("dbus.Interface")
    def test_wrong_response(self, _, null):
        dbus.SystemBus.return_value = namedtuple(
            "miner_bus",
            "get_object")(get_object=lambda x, y: [])
        dbus.Interface.side_effect = dbus.exceptions.DBusException()
        res = get_miner_diagnostics()
        self.assertEqual(res,  ['no', '', '0', '', '0'])
