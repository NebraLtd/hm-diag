import unittest
import sys
from unittest.mock import mock_open, patch
sys.path.append("..")
from hw_diag.utilities.miner import get_public_keys  # noqa


class TestGetPublicKeys(unittest.TestCase):
    TEST_DATA = '{}\n{}\n{}'.format(
        '{pubkey, "112mPWkGW55kcbQTgbtJvgAKMSTrEhHgavrdF1Cbu8FU85tTL4Nc"}.',
        '{onboarding_key, '
        '"112mPWkGW55kcbQTgbtJvgAKMSTrEhHgavrdF1Cbu8FU85tTL142"}.',
        '{animal_name, "gigantic-basil-turtle"}.'
    )

    right_list = [
        '112mPWkGW55kcbQTgbtJvgAKMSTrEhHgavrdF1Cbu8FU85tTL4Nc',
        '112mPWkGW55kcbQTgbtJvgAKMSTrEhHgavrdF1Cbu8FU85tTL142',
        'gigantic-basil-turtle']

    # @patch("builtins.open", new_callable=mock_open, read_data=TEST_DATA)

    def test_get_keys(self):
        m = mock_open(read_data=self.TEST_DATA)
        with patch('builtins.open', m):
            result = get_public_keys()
            self.assertEqual(len(result), 3)
            for (res, right) in zip(result, self.right_list):
                self.assertEqual(res, right)

    def test_permissions_file(self):
        with patch("builtins.open", mock_open()) as mf:
            fh_mock = mf.return_value.__enter__.return_value
            fh_mock.write.side_effect = PermissionError
            get_public_keys()
            self.assertRaises(PermissionError)
