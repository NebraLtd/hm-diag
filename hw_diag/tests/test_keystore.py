import unittest
from unittest.mock import mock_open, patch
import os

from hw_diag.utilities.keystore import KeyStore

TEMP_FILE = '/tmp/mock_test.json'


class TestKeyStore(unittest.TestCase):

    def test_default_value_missing_file(self):
        fh = mock_open(read_data='{}')
        with patch('builtins.open', fh):
            fh_mock = fh.return_value.__enter__.return_value
            fh_mock.read.side_effect = FileNotFoundError
            ks = KeyStore(TEMP_FILE)
            default_value = ks.get('foo', default='bar')
            self.assertEqual(default_value, 'bar')

    def test_default_value_missing_key(self):
        fh = mock_open(read_data='{}')
        with patch('builtins.open', fh):
            ks = KeyStore(TEMP_FILE)
            default_value = ks.get('foo', default='bar')
            self.assertEqual(default_value, 'bar')

    def test_file_io(self):
        ks = KeyStore(TEMP_FILE)
        ks.set('foo', 'bar1')
        # read back the same object
        self.assertEqual(ks.get('foo'), 'bar1')
        # read a different object but same file
        ks1 = KeyStore(TEMP_FILE)
        self.assertEqual(ks1.get('foo'), 'bar1')
        self.assertTrue(os.path.exists(TEMP_FILE))
        os.remove(TEMP_FILE)
