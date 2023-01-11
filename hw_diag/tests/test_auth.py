import unittest

from unittest.mock import patch
from hw_diag.database.models.auth import AuthKeyValue

# Test Candidate
from hw_diag.utilities.auth import update_password
from hw_diag.utilities.auth import check_password


HASH = '$2b$12$W7hBbyMN/ccp/p59UGktee3ZDX7Eb7sJhJt0Tw4KC0swN07cQecd.'
PASSWD_ROW = AuthKeyValue(
    key='password_hash',
    value=HASH
)
PASSWD_STRING = 'P455w0rd!'


class TestDatabaseMigrations(unittest.TestCase):

    @patch("hw_diag.utilities.auth.check_password", return_value=True)
    @patch("hw_diag.utilities.auth.write_password")
    def test_update_good_password(
            self,
            mock_write_password,
            mock_check_password
    ):
        result = update_password(
            PASSWD_STRING,
            PASSWD_STRING,
            PASSWD_STRING
        )
        expected_result = {
            'error': False,
            'msg': 'Password updated successfully.'
        }
        self.assertEqual(
            result,
            expected_result
        )
        self.assertIsInstance(
            result,
            dict
        )

    @patch("hw_diag.utilities.auth.check_password", return_value=False)
    @patch("hw_diag.utilities.auth.write_password")
    def test_update_incorrect_original_password(
            self,
            mock_write_password,
            mock_check_password
    ):
        result = update_password(
            PASSWD_STRING,
            PASSWD_STRING,
            PASSWD_STRING
        )
        expected_result = {
            'error': True,
            'msg': 'Current password is not valid.'
        }
        self.assertEqual(
            result,
            expected_result
        )
        self.assertIsInstance(
            result,
            dict
        )

    @patch("hw_diag.utilities.auth.check_password", return_value=True)
    @patch("hw_diag.utilities.auth.write_password")
    def test_update_weak_new_password(
            self,
            mock_write_password,
            mock_check_password
    ):
        result = update_password(
            PASSWD_STRING,
            'weakpass',
            'weakpass'
        )
        expected_msg = (
            'Password is not complex enough, please ensure password is greater than 8 '
            'characters, has atleast 1 number, 1 uppercase character and 1 special character.'
        )
        expected_result = {
            'error': True,
            'msg': expected_msg
        }
        self.assertEqual(
            result,
            expected_result
        )
        self.assertIsInstance(
            result,
            dict
        )

    @patch("hw_diag.utilities.auth.check_password", return_value=True)
    @patch("hw_diag.utilities.auth.write_password")
    def test_update_invalid_confirmation_password(
            self,
            mock_write_password,
            mock_check_password
    ):
        result = update_password(
            PASSWD_STRING,
            'cH1ck3nnuGg3t5!',
            'incorrect'
        )
        expected_result = {
            'error': True,
            'msg': 'New password and password confirmation do not match.'
        }
        self.assertEqual(
            result,
            expected_result
        )
        self.assertIsInstance(
            result,
            dict
        )

    @patch("hw_diag.utilities.auth.read_password", return_value=PASSWD_ROW)
    def test_check_password_ok(self, mock_read_password):
        result = check_password('test123')
        self.assertTrue(result)

    @patch("hw_diag.utilities.auth.read_password", return_value=PASSWD_ROW)
    def test_check_password_incorrect(self, mock_read_password):
        result = check_password('incorrectpassword')
        self.assertFalse(result)
