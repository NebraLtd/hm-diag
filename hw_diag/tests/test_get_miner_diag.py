import unittest
from collections import namedtuple
import dbus
from unittest.mock import patch
import sys
sys.path.append("..")
from hw_diag.utilities.miner import get_miner_diagnostics # noqa


class TestGetMinerDiag(unittest.TestCase):
    @patch("dbus.SessionBus")
    @patch("dbus.Interface")
    def test_right_response(self, _, null):
        dbus.SessionBus.return_value = namedtuple(
            "miner_bus",
            "get_object")(get_object=lambda x, y: [])
        dbus.Interface.return_value = namedtuple(
            "miner_interface",
            "P2PStatus")(P2PStatus=lambda: [
                [1, 2, 3, 4],
                [5, 6, 7, 8],
                [9, 10, 11, 12],
                [13, 14, 15, 16]
            ])
        res = get_miner_diagnostics()
        self.assertEqual(res, ['2', '6', '14', '10'])

    @patch("dbus.SessionBus")
    @patch("dbus.Interface")
    def test_wrong_response(self, _, null):
        dbus.SessionBus.return_value = namedtuple(
            "miner_bus",
            "get_object")(get_object=lambda x, y: [])
        dbus.Interface.side_effect = dbus.exceptions.DBusException()
        res = get_miner_diagnostics()
        self.assertEqual(res,  ['no', '', '0', ''])
