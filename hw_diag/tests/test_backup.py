import tempfile
import hashlib
import yaml
import json
import os

import unittest
from unittest.mock import patch

from hw_diag.utilities.backup.myst import MystBackupRestore
from hw_diag.utilities.backup.thingsix import ThingsIXBackupRestore
from hw_diag.utilities.backup import update_backup_checkpoint, services_pending_backup
from hw_diag.utilities.crypto import empty_hash
from hw_diag.app import get_app


class PerformBackupTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.app = get_app('test_app', lean_initializations=False)

        # myst plugin back dir and plugin
        self.temp_backup_dir = tempfile.TemporaryDirectory()
        self.myst_backup_plugin = MystBackupRestore(self.temp_backup_dir.name)

        # myst storage dir and keystore dir
        self.temp_myst_dir = tempfile.TemporaryDirectory()
        self.temp_myst_keystore_dirname = f'{self.temp_myst_dir.name}/keystore'
        os.mkdir(self.temp_myst_keystore_dirname)

        # thingsix plugin
        self.thingsix_backup_plugin = ThingsIXBackupRestore(self.temp_backup_dir.name)

        # thingsix storage dir and keystore dir
        self.temp_thingsix_dir = tempfile.TemporaryDirectory()

        # temp data
        self.myst_json = {
            "address": "1e775ed21d80b37368ea9334dc1da2a843sfsdfwe",
            "crypto": {
                "cipher": "aes-128-ctr",
                "ciphertext": "885657ccdcc14ea3d1c507ded4bc61ea7ba0adf28448f48461089e054d1ea324",
                "cipherparams": {
                    "iv": "44eb243edbe6e3e46a1f788940d53bb2"
                },
                "kdf": "scrypt",
                "kdfparams": {
                    "dklen": 32,
                    "n": 4096,
                    "p": 6,
                    "r": 8,
                    "salt": "a2a246a5386ff33c312420c36403650930703b0fec0a7e2b771ea79335c9e214"
                },
                "mac": "eb96c96618d85fffcefc8c163d880971c6ddc71cbf5abedb4322f4f5630231242"
            },
            "id": "3bb7a107-6089-44d4-9f54-9176f50fsdfsdf",
            "version": 3
        }
        self.myst_json_str = json.dumps(self.myst_json).encode()
        self.myst_hash = hashlib.sha256(self.myst_json_str).hexdigest()

        # thingsix id data
        self.thingsix_yaml = [
            {
                "local_id": "0000ee6aeb9ad0bf",
                "private_key": "46e22dfc15cf4a548269143da6cd17cfa7c6eb1c900ace4ffd08987f6aadd432"
            }
        ]
        self.thingsix_str = yaml.dump(self.thingsix_yaml).encode()
        self.thingsix_hash = hashlib.sha256(self.thingsix_str).hexdigest()

    def tearDown(self):
        self.temp_backup_dir.cleanup()

    def test_myst_identity_hash_with_valid_json(self):
        with patch('hw_diag.utilities.backup.myst.MYST_DIR', self.temp_myst_dir.name):
            # write the mocked data to file
            temp_file = tempfile.NamedTemporaryFile(dir=self.temp_myst_keystore_dirname,
                                                    prefix='UTC', delete=False)
            print(temp_file.name)
            temp_file.write(self.myst_json_str)
            temp_file.close()

            # verify
            expected_result = {'Mysterium': self.myst_hash}
            actual_result = self.myst_backup_plugin.identity_hash()
            self.assertEqual(expected_result, actual_result)
            os.remove(temp_file.name)

    def test_myst_identity_hash_with_invalid_json(self):
        with patch('hw_diag.utilities.backup.myst.MYST_DIR', self.temp_myst_dir.name):
            # write the mocked data to file
            temp_file = tempfile.NamedTemporaryFile(dir=self.temp_myst_keystore_dirname,
                                                    prefix='UTC', delete=False)
            print(temp_file.name)
            temp_file.write(b'invalid_json')
            temp_file.close()

            # verify
            expected_result = {'Mysterium': empty_hash()}
            actual_result = self.myst_backup_plugin.identity_hash()
            self.assertEqual(expected_result, actual_result)
            os.remove(temp_file.name)

    def test_myst_identity_hash_with_no_files(self):
        with patch('hw_diag.utilities.backup.myst.MYST_DIR', self.temp_myst_dir.name):
            # verify
            expected_result = {'Mysterium': empty_hash()}
            actual_result = self.myst_backup_plugin.identity_hash()
            self.assertEqual(expected_result, actual_result)

    def test_thingsix_identity_hash_with_valid_yaml(self):
        with patch('hw_diag.utilities.backup.thingsix.THIX_DIR', self.temp_thingsix_dir.name):
            # write the mocked data to file
            with open(f"{self.temp_thingsix_dir.name}/gateways.yaml", 'wb') as temp_file:
                temp_file.write(self.thingsix_str)

            expected_result = {'Thingsix': self.thingsix_hash}
            actual_result = self.thingsix_backup_plugin.identity_hash()
            self.assertEqual(expected_result, actual_result)
            os.remove(temp_file.name)

    def test_thingsix_identity_hash_with_invalid_yaml(self):
        with patch('hw_diag.utilities.backup.thingsix.THIX_DIR', self.temp_thingsix_dir.name):
            # write the mocked data to file
            with open(f"{self.temp_thingsix_dir.name}/gateways.yaml", 'wb') as temp_file:
                temp_file.write(b"")

            expected_result = {'Thingsix': empty_hash()}
            actual_result = self.thingsix_backup_plugin.identity_hash()
            self.assertEqual(expected_result, actual_result)
            os.remove(temp_file.name)

    def test_thingsix_identity_hash_with_no_files(self):
        with patch('hw_diag.utilities.backup.thingsix.THIX_DIR', self.temp_thingsix_dir.name):
            expected_result = {'Thingsix': empty_hash()}
            actual_result = self.thingsix_backup_plugin.identity_hash()
            self.assertEqual(expected_result, actual_result)

    @patch('hw_diag.utilities.backup.set_value')
    @patch('hw_diag.utilities.backup.identity_hashes')
    def test_update_backup_checkpoint(self, mock_identity_hashes, mock_set_value):
        with self.app.app_context():
            mock_identity_hashes.return_value = {
                'Thingsix': 'e1f710d70188be017a403f0c3816e3cffcf8e95f9e3e08e41d2fb6de48fe0ce2',
                'Mysterium': 'e1f710d70188be017a403f0c3816e3cffcf8e95f9e3e08e41d2fb6de48fe0cz2'
            }
            update_backup_checkpoint()
            self.assertEqual(mock_set_value.call_count, 2)

    @patch('hw_diag.utilities.backup.get_value')
    @patch('hw_diag.utilities.backup.identity_hashes')
    def test_services_pending_backup(self, mock_identity_hashes, mock_get_value):
        mock_identity_hashes.return_value = {'service': 'new_hash'}
        mock_get_value.return_value = 'old_hash'
        expected = ['service']
        actual = services_pending_backup()
        self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
