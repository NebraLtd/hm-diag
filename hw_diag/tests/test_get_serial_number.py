import unittest
import sys
from unittest.mock import mock_open, patch
sys.path.append("..")
from hw_diag.utilities.hardware import get_serial_number  # noqa


class TestGetPublicKeys(unittest.TestCase):

    TEST_DATA = """00000000a3e7kg80"""

    right_value = {'serial_number': '00000000a3e7kg80'}
    diag = {}

    def test_get_serialnumber(self):
        m = mock_open(read_data=''.join(self.TEST_DATA))
        with patch('builtins.open', m):
            get_serial_number(self.diag)
            self.assertEqual(self.diag["serial_number"],
                             self.right_value["serial_number"])

    def test_available_file(self):
        with patch("builtins.open", mock_open(read_data=self.TEST_DATA)) as mf:
            fh_mock = mf.return_value.__enter__.return_value
            fh_mock.write.side_effect = FileNotFoundError
            get_serial_number(self.diag)
            self.assertRaises(FileNotFoundError)

    def test_permissions_error(self):
        with patch("builtins.open", mock_open(read_data=self.TEST_DATA)) as mf:
            fh_mock = mf.return_value.__enter__.return_value
            fh_mock.write.side_effect = PermissionError
            get_serial_number(self.diag)
            self.assertRaises(PermissionError)
