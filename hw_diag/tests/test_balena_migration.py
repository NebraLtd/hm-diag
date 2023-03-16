import unittest
from unittest.mock import patch
import os
import json
import responses
import tempfile

from hw_diag.utilities.balena_migration import attempt_device_migration, \
    DASHBOARD_ENDPOINT, is_cloud_migration
from hw_diag.tests.fixtures.balena_migration_data import TEST_DATA


MOCKED_SERIAL_NUMBER = 'bdfdgfd654huyt6hu7'
FULL_DASHBOARD_URL = f'{DASHBOARD_ENDPOINT}/{MOCKED_SERIAL_NUMBER}'


def add_response(status_code, data):
    responses.add(
        responses.PATCH,
        FULL_DASHBOARD_URL,
        status=status_code,
        json=data
    )


class TestBalenaMigration(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.temp_boot = f'{self.tempdir.name}/boot'
        self.config_json = f'{self.temp_boot}/config.json'
        self.temp_config_json = f'{self.config_json}_temp'

        if not os.path.exists(self.temp_boot):
            os.mkdir(self.temp_boot)

        return super().setUp()

    @responses.activate
    @patch("hw_diag.utilities.balena_migration.fetch_serial_number",
           return_value=MOCKED_SERIAL_NUMBER)
    @patch("hw_diag.utilities.balena_migration.mount_boot_partition")
    @patch("hw_diag.utilities.balena_supervisor.BalenaSupervisor.reboot")
    @patch.dict(
        os.environ,
        {
            'BALENA_SUPERVISOR_ADDRESS': 'localhost',
            'BALENA_SUPERVISOR_API_KEY': 'aabbffe',
            'BALENA_APP_ID': '0011223'
        }
    )
    def test_config_update_success(self, mock_supervisor, mock_boot_partiton, mock_serial):
        with patch('hw_diag.utilities.balena_migration.BOOT_MOUNT_POINT', self.temp_boot):
            with patch('hw_diag.utilities.balena_migration.CONFIG_FILENAME', self.config_json):
                with patch('hw_diag.utilities.balena_migration.CONFIG_TEMP_FILENAME',
                           self.temp_config_json):
                    # write old config to file
                    supervisor_call_count = 0
                    for configs in TEST_DATA:
                        open(self.config_json, 'w').write(json.dumps(configs[0]))
                        add_response(configs[1], configs[2])
                        # migrate
                        attempt_device_migration()
                        # read back new config and verify
                        written_content = open(self.config_json, 'r').read()
                        data = json.loads(written_content)
                        expected = configs[3]
                        self.assertEqual(data, expected)

                        if configs[1] == 200:
                            supervisor_call_count += 1
                            self.assertEqual(mock_supervisor.call_count, supervisor_call_count)
                        else:
                            self.assertEqual(mock_supervisor.call_count, supervisor_call_count)

    def test_no_boot_parition(self):
        # mount process will result in type error because of None type passed as mount point
        with self.assertRaises(TypeError):
            attempt_device_migration()

    def test_is_cloud_migration(self):
        balena_cloud_api_endpoint = "https://api.balena-cloud.com"
        nebra_cloud_api_endpoint = "https://api.cloud.nebra.com"

        old_config = {"apiEndpoint": balena_cloud_api_endpoint}
        new_config = {"apiEndpoint": nebra_cloud_api_endpoint}
        self.assertTrue(is_cloud_migration(old_config, new_config))

        old_config['apiEndpoint'] = nebra_cloud_api_endpoint
        new_config['apiEndpoint'] = nebra_cloud_api_endpoint
        self.assertFalse(is_cloud_migration(old_config, new_config))
