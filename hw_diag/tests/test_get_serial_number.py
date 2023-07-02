import unittest
import pytest

from unittest.mock import mock_open, patch
from hw_diag.utilities.hardware import get_serial_number, load_serial_number, \
    load_cpu_info, has_valid_serial

TEST_SERIAL = "00000000a3e7kg80"
TEST_SERIAL_ALL_ZERO = "000000000000000000000000000000"
TEST_SERIAL_ROCKPI = "d18dbe5c2a58cc61"
TEST_SERIAL_BOBCAT = "ba033cbdca6d626f"
TEST_SERIAL_RASPI = "000000009e3cb787"
TEST_SERIAL_ROCKPI_WRONG = "W1EP3DN9PU"
TEST_SERIAL_BOBCAT_WRONG = "c3d9b8674f4b94f6"
TEST_SERIAL_SHORT = "123ABC"
TEST_SERIAL_EMPTY = ""

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
SERIAL_VALID = {'serial': '912558f1a3ae877dabcdef1234567890ABCDEF'}
SERIAL_ALL_ZERO = {'serial': '000000000000000'}
SERIAL_WRONG_ROCKPI = {'serial': 'CKHZ4CHI1P'}
SERIAL_WRONG_BOBCAT = {'serial': 'c3d9b8674f4b94f6'}
SERIAL_NON_HEX_TEN_DIGITS = {'serial': 'XXXYYYZZZZ'}
SERIAL_SHORT = {'serial': 'ABC123abc'}
SERIAL_BLANK = {'serial': ''}
SERIAL_MISSING = {}
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

    def test_has_valid_serial_all_zeros(self):
            self.assertFalse(has_valid_serial(SERIAL_ALL_ZERO))

    def test_has_valid_serial_non_hex(self):
            self.assertFalse(has_valid_serial(SERIAL_NON_HEX_TEN_DIGITS))

    def test_has_valid_serial_knonwn_wrong(self):
            self.assertFalse(has_valid_serial(SERIAL_WRONG_ROCKPI))

    def test_has_valid_serial_knonwn_wrong(self):
            self.assertFalse(has_valid_serial(SERIAL_WRONG_BOBCAT))

    def test_has_valid_serial_mising(self):
            self.assertFalse(has_valid_serial(SERIAL_MISSING))

    def test_has_valid_serial_blank(self):
            self.assertFalse(has_valid_serial(SERIAL_BLANK))

    def test_has_valid_serial_short(self):
            self.assertFalse(has_valid_serial(SERIAL_SHORT))

    def test_has_valid_serial_true(self):
            self.assertTrue(has_valid_serial(SERIAL_VALID))

    @patch('hw_diag.utilities.hardware.is_rockpi')
    @patch('hw_diag.utilities.hardware.load_cpu_info')
    @patch('hw_diag.utilities.hardware.load_serial_number')
    def test_get_serial_number_rockpi(self, mock_serial, mock_cpuinfo, mock_rockpi):
        mock_rockpi.return_value = True
        mock_cpuinfo.return_value = {'serial': TEST_SERIAL_ROCKPI}
        mock_serial.return_value = {'serial': TEST_SERIAL_ROCKPI_WRONG}

        right_value = {'serial_number': 'd18dbe5c2a58cc61'}
        get_serial_number(self.diag)
        self.assertEqual(self.diag["serial_number"],
                         right_value["serial_number"])

        mock_rockpi.assert_called_once()
        mock_cpuinfo.assert_called_once()
        mock_serial.assert_called_once()

    @patch('hw_diag.utilities.hardware.is_rockpi')
    @patch('hw_diag.utilities.hardware.load_cpu_info')
    @patch('hw_diag.utilities.hardware.load_serial_number')
    def test_get_serial_number_all_zero(self, mock_serial, mock_cpuinfo, mock_rockpi):
        mock_rockpi.return_value = True
        mock_cpuinfo.return_value = {'serial': TEST_SERIAL_ALL_ZERO}
        mock_serial.return_value = {'serial': TEST_SERIAL_ALL_ZERO}

        right_value = {'serial_number': 'Serial number not found'}
        get_serial_number(self.diag)
        self.assertEqual(self.diag["serial_number"],
                         right_value["serial_number"])

        mock_cpuinfo.assert_called_once()
        mock_serial.assert_called_once()
        self.assertEqual(mock_rockpi.call_count, 2)

    @patch('hw_diag.utilities.hardware.is_rockpi')
    @patch('hw_diag.utilities.hardware.load_cpu_info')
    @patch('hw_diag.utilities.hardware.load_serial_number')
    def test_get_serial_number_rockpi_raspi(self, mock_serial, mock_cpuinfo, mock_rockpi):
        mock_rockpi.return_value = True
        mock_cpuinfo.return_value = {'serial': TEST_SERIAL_ROCKPI}
        mock_serial.return_value = {'serial': TEST_SERIAL}

        right_value = {'serial_number': 'd18dbe5c2a58cc61'}
        get_serial_number(self.diag)
        self.assertEqual(self.diag["serial_number"],
                         right_value["serial_number"])

        mock_rockpi.assert_called_once()
        mock_cpuinfo.assert_called_once()
        mock_serial.assert_called_once()

    @patch('hw_diag.utilities.hardware.is_rockpi')
    @patch('hw_diag.utilities.hardware.load_cpu_info')
    @patch('hw_diag.utilities.hardware.load_serial_number')
    def test_get_serial_number_short_wrong(self, mock_serial, mock_cpuinfo, mock_rockpi):
        mock_rockpi.return_value = False
        mock_cpuinfo.return_value = {'serial': TEST_SERIAL_SHORT}
        mock_serial.return_value = {'serial': TEST_SERIAL_BOBCAT_WRONG}

        right_value = {'serial_number': 'Serial number not found'}
        get_serial_number(self.diag)
        self.assertEqual(self.diag["serial_number"],
                         right_value["serial_number"])

        mock_cpuinfo.assert_called_once()
        mock_serial.assert_called_once()
        self.assertEqual(mock_rockpi.call_count, 2)

    @patch('hw_diag.utilities.hardware.is_rockpi')
    @patch('hw_diag.utilities.hardware.load_cpu_info')
    @patch('hw_diag.utilities.hardware.load_serial_number')
    def test_get_serial_number_raspi_rockpi(self, mock_serial, mock_cpuinfo, mock_rockpi):
        mock_rockpi.return_value = False
        mock_cpuinfo.return_value = {'serial': TEST_SERIAL_ROCKPI}
        mock_serial.return_value = {'serial': TEST_SERIAL}

        right_value = {'serial_number': '00000000a3e7kg80'}
        get_serial_number(self.diag)
        self.assertEqual(self.diag["serial_number"],
                         right_value["serial_number"])

        mock_rockpi.assert_called_once()
        mock_cpuinfo.assert_called_once()
        mock_serial.assert_called_once()

    @patch('hw_diag.utilities.hardware.is_rockpi')
    @patch('hw_diag.utilities.hardware.load_cpu_info')
    @patch('hw_diag.utilities.hardware.load_serial_number')
    def test_get_serial_number_raspi(self, mock_serial, mock_cpuinfo, mock_rockpi):
        mock_rockpi.return_value = False
        mock_cpuinfo.return_value = {'serial': TEST_SERIAL}
        mock_serial.return_value = {'serial': TEST_SERIAL}

        right_value = {'serial_number': '00000000a3e7kg80'}
        get_serial_number(self.diag)
        self.assertEqual(self.diag["serial_number"],
                         right_value["serial_number"])

        mock_rockpi.assert_called_once()
        mock_cpuinfo.assert_called_once()
        mock_serial.assert_called_once()

    @patch('hw_diag.utilities.hardware.is_rockpi')
    @patch('hw_diag.utilities.hardware.load_cpu_info')
    @patch('hw_diag.utilities.hardware.load_serial_number')
    def test_get_serial_number_bobcat(self, mock_serial, mock_cpuinfo, mock_rockpi):
        mock_rockpi.return_value = False
        mock_cpuinfo.return_value = {'serial': TEST_SERIAL_BOBCAT}
        mock_serial.return_value = {'serial': TEST_SERIAL_BOBCAT_WRONG}

        right_value = {'serial_number': 'ba033cbdca6d626f'}
        get_serial_number(self.diag)
        self.assertEqual(self.diag["serial_number"],
                         right_value["serial_number"])

        mock_rockpi.assert_called_once()
        mock_cpuinfo.assert_called_once()
        mock_serial.assert_called_once()

    @patch('hw_diag.utilities.hardware.is_rockpi')
    @patch('hw_diag.utilities.hardware.load_cpu_info')
    @patch('hw_diag.utilities.hardware.load_serial_number')
    def test_get_serial_number_rockpi_zero(self, mock_serial, mock_cpuinfo, mock_rockpi):
        mock_rockpi.return_value = True
        mock_cpuinfo.return_value = {'serial': TEST_SERIAL_ALL_ZERO}
        mock_serial.return_value = {'serial': TEST_SERIAL_ROCKPI}

        right_value = {'serial_number': 'd18dbe5c2a58cc61'}
        get_serial_number(self.diag)
        self.assertEqual(self.diag["serial_number"],
                         right_value["serial_number"])

        mock_cpuinfo.assert_called_once()
        mock_serial.assert_called_once()
        self.assertEqual(mock_rockpi.call_count, 2)

    @patch('hw_diag.utilities.hardware.is_rockpi')
    @patch('hw_diag.utilities.hardware.load_cpu_info')
    @patch('hw_diag.utilities.hardware.load_serial_number')
    def test_get_serial_number_rockpi_backwards(self, mock_serial, mock_cpuinfo, mock_rockpi):
        mock_rockpi.return_value = True
        mock_cpuinfo.return_value = {'serial': TEST_SERIAL}
        mock_serial.return_value = {'serial': TEST_SERIAL_ROCKPI}

        right_value = {'serial_number': '00000000a3e7kg80'}
        get_serial_number(self.diag)
        self.assertEqual(self.diag["serial_number"],
                         right_value["serial_number"])

        mock_rockpi.assert_called_once()
        mock_cpuinfo.assert_called_once()
        mock_serial.assert_called_once()

    @patch('hw_diag.utilities.hardware.is_rockpi')
    @patch('hw_diag.utilities.hardware.load_cpu_info')
    @patch('hw_diag.utilities.hardware.load_serial_number')
    def test_get_serial_number_raspi_empty(self, mock_serial, mock_cpuinfo, mock_rockpi):
        mock_rockpi.return_value = False
        mock_cpuinfo.return_value = {'serial': TEST_SERIAL}
        mock_serial.return_value = {'serial': TEST_SERIAL_EMPTY}

        right_value = {'serial_number': '00000000a3e7kg80'}
        get_serial_number(self.diag)
        self.assertEqual(self.diag["serial_number"],
                         right_value["serial_number"])

        mock_rockpi.assert_called_once()
        mock_cpuinfo.assert_called_once()
        mock_serial.assert_called_once()

    @patch('hw_diag.utilities.hardware.is_rockpi')
    @patch('hw_diag.utilities.hardware.load_cpu_info')
    @patch('hw_diag.utilities.hardware.load_serial_number')
    @patch('hw_diag.utilities.hardware.has_valid_serial')
    def test_has_valid_serial_called(self, mock_valid_serial, mock_serial, mock_cpuinfo, mock_rockpi):
        mock_rockpi.return_value = False
        mock_cpuinfo.return_value = {'serial': TEST_SERIAL}
        mock_serial.return_value = {'serial': TEST_SERIAL_EMPTY}
        
        get_serial_number(self.diag)
        mock_valid_serial.assert_called_once()
