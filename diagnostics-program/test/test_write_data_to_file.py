import unittest
import sys
from unittest.mock import mock_open, patch
import subprocess
sys.path.append("..")
from main import writing_data # noqa


class TestWriteDataToFile(unittest.TestCase):
    def setUp(self):
        self.path = "file.txt"
        self.write_data = "test data"

    def test_clear_write(self):
        writing_data(self.path, self.write_data)
        with open(self.path, 'r') as file:
            data = file.read()
        self.assertEqual(data, self.write_data)

    def test_wrong_path_type(self):
        self.assertRaises(TypeError, writing_data, 432, self.write_data)

    def test_wrong_directory_path(self):
        self.assertRaises(
            FileNotFoundError,
            writing_data,
            f"/some/path/{self.path}",
            self.write_data)

    def test_permissions_error(self):
        with patch("builtins.open", mock_open()) as mf:
            fh_mock = mf.return_value.__enter__.return_value
            fh_mock.write.side_effect = PermissionError
            self.assertRaises(
                PermissionError,
                writing_data,
                self.path,
                self.write_data)

    def tearDown(self):
        subprocess.call(['rm', '-rf', self.path])
