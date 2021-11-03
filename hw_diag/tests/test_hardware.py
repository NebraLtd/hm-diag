import unittest
from unittest.mock import patch
from hw_diag.utilities.hardware import get_public_keys_and_ignore_errors # noqa


class TestHardware(unittest.TestCase):
    @patch('hw_diag.utilities.hardware.get_public_keys_rust')
    def test_get_public_keys_no_error(self, mocked_get_public_keys_rust):
        mocked_get_public_keys_rust.return_value = {
            'key': 'foo',
            'name': 'bar'
        }
        keys = get_public_keys_and_ignore_errors()

        self.assertEqual(keys['key'], 'foo')
        self.assertEqual(keys['name'], 'bar')

    @patch('hw_diag.utilities.hardware.get_public_keys_rust')
    def test_get_public_keys_with_error(self, mocked_get_public_keys_rust):
        mocked_get_public_keys_rust.return_value = False
        keys = get_public_keys_and_ignore_errors()

        self.assertEqual(keys['key'], 'ECC failure')
        self.assertEqual(keys['name'], 'ECC failure')
