import unittest
import pytest

from unittest.mock import mock_open, patch
from hw_diag.utilities.hardware import get_serial_number, load_serial_number, \
    load_cpu_info

TEST_SERIAL = "00000000a3e7kg80"

TEST_CPU_INFO = """
processor	: 0
BogoMIPS	: 48.00
Features	: fp asimd evtstrm aes pmull sha1 sha2 crc32
CPU implementer	: 0x41
CPU architecture: 8
CPU variant	: 0x0
CPU part	: 0xd04
CPU revision	: 2

Serial		: 912558f1a3ae877d
"""

TEST_SERIAL_NUMBER_RESULT = {'serial': '00000000a3e7kg80'}
TEST_CPU_INFO_RESULT = {'serial': '912558f1a3ae877d'}
FAILED_CPU_INFO_RESULT = {}
FAILED_SERIAL_NUMBER_RESULT = {}

class TestGetSerialNumber(unittest.TestCase):

    right_value = {'serial_number': '00000000a3e7kg80'}
    diag = {}

    @pytest.fixture(autouse=True)
    def _pass_fixtures(self, caplog):
        self.caplog = caplog

    def test_get_serialnumber(self):
        m = mock_open(read_data=TEST_SERIAL)
        with patch("builtins.open", m):
            get_serial_number(self.diag)
            self.assertEqual(self.diag["serial_number"],
                             self.right_value["serial_number"])

    def test_strip_serialnumber(self):
        m = mock_open(read_data="%s\x00" % TEST_SERIAL)
        with patch("builtins.open", m):
            get_serial_number(self.diag)
            self.assertEqual(self.diag["serial_number"],
                             self.right_value["serial_number"])

    def test_available_file(self):
        with patch("builtins.open", mock_open(read_data=TEST_SERIAL)) as mf:
            fh_mock = mf.return_value.__enter__.return_value
            fh_mock.write.side_effect = FileNotFoundError
            get_serial_number(self.diag)
            self.assertRaises(FileNotFoundError)

    def test_permissions_error(self):
        with patch("builtins.open", mock_open(read_data=TEST_SERIAL)) as mf:
            fh_mock = mf.return_value.__enter__.return_value
            fh_mock.write.side_effect = PermissionError
            get_serial_number(self.diag)
            self.assertRaises(PermissionError)

    def test_load_serial_number(self):
        with patch("builtins.open", mock_open(read_data=TEST_SERIAL)):
            serial = load_serial_number()
            self.assertEqual(serial["serial"], TEST_SERIAL_NUMBER_RESULT["serial"])

    def test_load_serial_number_fail(self):
        with patch("builtins.open", mock_open()) as mf:
            mf.side_effect = FileNotFoundError()

            serial = load_serial_number()
            captured = self.caplog
            self.assertTrue('failed to load /proc/device-tree/serial-number' in str(captured.text))
            self.assertEqual(serial, FAILED_SERIAL_NUMBER_RESULT)

    def test_load_cpuinfo(self):
        with patch("builtins.open", mock_open(read_data=TEST_CPU_INFO)):
            cpuinfo = load_cpu_info()
            self.assertEqual(cpuinfo["serial"], TEST_CPU_INFO_RESULT["serial"])

    def test_load_cpuinfo_fail(self):
        with patch("builtins.open", mock_open()) as mf:
            mf.side_effect = FileNotFoundError()
            
            cpuinfo = load_cpu_info()
            captured = self.caplog
            self.assertTrue('failed to load /proc/cpuinfo' in str(captured.text))
            self.assertEqual(cpuinfo, FAILED_CPU_INFO_RESULT)
