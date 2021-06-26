import unittest
import sys
from unittest.mock import mock_open, patch
sys.path.append("..")
from utils import get_rpi_serial  # noqa


class TestGetPublicKeys(unittest.TestCase):

    TEST_DATA = """Revision        : a020d3
Serial\t\t: 00000000a3e7kg80
Model           : Raspberry Pi 3 Model B Plus Rev 1.3 """

    right_value = {'RPI': '00000000a3e7kg80'}
    diag = {}

    def test_get_rpi(self):
        m = mock_open(read_data=''.join(self.TEST_DATA))
        with patch('builtins.open', m):
            get_rpi_serial(self.diag)
            self.assertEqual(self.diag["RPI"], self.right_value["RPI"])

    def test_available_file(self):
        with patch("builtins.open", mock_open(read_data=self.TEST_DATA)) as mf:
            fh_mock = mf.return_value.__enter__.return_value
            fh_mock.write.side_effect = FileNotFoundError
            get_rpi_serial(self.diag)
            self.assertRaises(FileNotFoundError)

    def test_permissions_error(self):
        with patch("builtins.open", mock_open(read_data=self.TEST_DATA)) as mf:
            fh_mock = mf.return_value.__enter__.return_value
            fh_mock.write.side_effect = PermissionError
            get_rpi_serial(self.diag)
            self.assertRaises(PermissionError)
