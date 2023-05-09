import unittest
from unittest.mock import patch

import responses
from requests.exceptions import ConnectionError, ConnectTimeout

from hw_diag.utilities.balena_cloud import BalenaCloud
from hw_diag.utilities import balena_cloud


TEST_API_URL = 'http://127.0.0.1'
TEST_API_KEY = 'secret'
TEST_APP_ID = '12345'
TEST_DEVICE_ID = 123456
TEST_DEVICE_UUID = '123456789abcd'
TEST_VAR_ID = 10
TEST_GET_DEVICE_ID_URL = f'http://127.0.0.1/v6/device?$filter=uuid%20eq%20\'{TEST_DEVICE_UUID}\''
TEST_GET_FLEET_CONFIG_VARIABLES_URL = (
    f'http://127.0.0.1/v6/application_config_variable?$filter=application%20eq%20{TEST_APP_ID}'
)
TEST_GET_DEVICE_CONFIG_VARIABLES_URL = (
    f'http://127.0.0.1/v6/device_config_variable?$filter=device%20eq%20{TEST_DEVICE_ID}'
)
TEST_CREATE_DEVICE_CONFIG_VARIABLE_URL = 'http://127.0.0.1/v6/device_config_variable'
TEST_UPDATE_DEVICE_CONFIG_VARIABLE_URL = (
    f'http://127.0.0.1/v6/device_config_variable({TEST_VAR_ID})'
)
TEST_REMOVE_DEVICE_CONFIG_VARIABLE_URL = (
    f'http://127.0.0.1/v6/device_config_variable({TEST_VAR_ID})'
)
CONNECTION_EXCEPTION_MSG = 'Timout trying to make connection.'
TEST_VARIABLES = [
    {'id': 10, 'name': 'TEST_VAR_1', 'value': 'test-value-1'},
    {'id': 20, 'name': 'TEST_VAR_2', 'value': 'test-value-2'},
]


class TestBalenaCloud(unittest.TestCase):

    @staticmethod
    def make_balena_cloud():
        return BalenaCloud(
            TEST_API_URL,
            TEST_API_KEY,
            TEST_APP_ID,
            TEST_DEVICE_UUID,
        )

    def test_creation(self):
        """Should create a `BalenaCloud` object with attributes set from arguments passed
        to `__init__()`."""

        bc = self.make_balena_cloud()

        assert bc.api_url == TEST_API_URL
        assert bc.app_id == TEST_APP_ID
        assert bc.device_uuid == TEST_DEVICE_UUID
        assert bc.headers == {
            'Content-type': 'application/json',
            'Authorization': f'Bearer {TEST_API_KEY}'
        }

    @patch.dict(
        balena_cloud.os.environ,
        {
            'BALENA_API_URL': TEST_API_URL,
            'BALENA_API_KEY': TEST_API_KEY,
            'BALENA_APP_ID': TEST_APP_ID,
            'BALENA_DEVICE_UUID': TEST_DEVICE_UUID,
        },
        clear=True
    )
    def test_creation_from_env(self):
        """Should create a `BalenaCloud` object with attributes properly set from corresponding
        env variables."""

        bc = BalenaCloud.new_from_env()

        assert bc.api_url == TEST_API_URL
        assert bc.app_id == TEST_APP_ID
        assert bc.device_uuid == TEST_DEVICE_UUID
        assert bc.headers == {
            'Content-type': 'application/json',
            'Authorization': f'Bearer {TEST_API_KEY}'
        }

    @responses.activate
    def test_get_device_id_success_response(self):
        """Should make an API call to Balena cloud and return the device ID received in response."""

        responses.add(
            responses.GET,
            TEST_GET_DEVICE_ID_URL,
            status=200,
            json={'d': [{'id': TEST_DEVICE_ID}]}
        )

        bc = self.make_balena_cloud()

        assert bc.get_device_id() == TEST_DEVICE_ID

    @responses.activate
    def test_get_device_id_cache(self):
        """Should call private `_get_device_id()` only once, caching the result afterwards."""

        responses.add(
            responses.GET,
            TEST_GET_DEVICE_ID_URL,
            status=200,
            json={'d': [{'id': TEST_DEVICE_ID}]}
        )

        bc = self.make_balena_cloud()
        with patch.object(bc, '_get_device_id') as spy_get_device_id_private:
            bc.get_device_id()
            bc.get_device_id()
        spy_get_device_id_private.assert_called_once()

    @responses.activate
    def test_get_device_id_connection_error(self):
        """Should make an API call to Balena cloud and raise `RuntimeError` due to API connection
        problem."""

        responses.add(
            responses.GET,
            TEST_GET_DEVICE_ID_URL,
            body=ConnectionError('Unable to connect')
        )

        bc = self.make_balena_cloud()

        with self.assertRaises(RuntimeError) as exp:
            bc.get_device_id()

        assert str(exp.exception).startswith('Device ID unavailable')

    @responses.activate
    def test_get_device_id_connection_timeout(self):
        """Should make an API call to Balena cloud and raise `RuntimeError` due to API connection
        timeout."""

        responses.add(
            responses.GET,
            TEST_GET_DEVICE_ID_URL,
            body=ConnectTimeout(CONNECTION_EXCEPTION_MSG)
        )

        bc = self.make_balena_cloud()

        with self.assertRaises(RuntimeError) as exp:
            bc.get_device_id()

        assert str(exp.exception).startswith('Device ID unavailable')

    @responses.activate
    def test_get_device_id_empty_response(self):
        """Should make an API call to Balena cloud and raise `RuntimeError` due to emtpy response
        from API."""

        responses.add(
            responses.GET,
            TEST_GET_DEVICE_ID_URL,
            body='',
            status=200
        )

        bc = self.make_balena_cloud()

        with self.assertRaises(RuntimeError) as exp:
            bc.get_device_id()

        assert str(exp.exception).startswith('Device ID unavailable')

    @responses.activate
    def test_get_fleet_config_variables_success_response(self):
        """Should make an API call to Balena cloud and return the fleet config variables received
        in response."""

        responses.add(
            responses.GET,
            TEST_GET_FLEET_CONFIG_VARIABLES_URL,
            status=200,
            json={'d': TEST_VARIABLES}
        )

        bc = self.make_balena_cloud()

        assert bc.get_fleet_config_variables() == TEST_VARIABLES

    @responses.activate
    def test_get_fleet_config_variables_connection_error(self):
        """Should make an API call to Balena cloud and raise `RuntimeError` due to API connection
        problem."""

        responses.add(
            responses.GET,
            TEST_GET_FLEET_CONFIG_VARIABLES_URL,
            body=ConnectionError('Unable to connect')
        )

        bc = self.make_balena_cloud()

        with self.assertRaises(RuntimeError) as exp:
            bc.get_fleet_config_variables()

        assert str(exp.exception).startswith('Failed to retrieve fleet config variables')

    @responses.activate
    def test_get_fleet_config_variables_connection_timeout(self):
        """Should make an API call to Balena cloud and raise `RuntimeError` due to API connection
        timeout."""

        responses.add(
            responses.GET,
            TEST_GET_FLEET_CONFIG_VARIABLES_URL,
            body=ConnectTimeout(CONNECTION_EXCEPTION_MSG)
        )

        bc = self.make_balena_cloud()

        with self.assertRaises(RuntimeError) as exp:
            bc.get_fleet_config_variables()

        assert str(exp.exception).startswith('Failed to retrieve fleet config variables')

    @responses.activate
    def test_get_fleet_config_variables_empty_response(self):
        """Should make an API call to Balena cloud and raise `RuntimeError` due to emtpy response
        from API."""

        responses.add(
            responses.GET,
            TEST_GET_FLEET_CONFIG_VARIABLES_URL,
            body='',
            status=200
        )

        bc = self.make_balena_cloud()

        with self.assertRaises(RuntimeError) as exp:
            bc.get_fleet_config_variables()

        assert str(exp.exception).startswith('Failed to retrieve fleet config variables')

    @responses.activate
    def test_get_device_config_variables_success_response(self):
        """Should make an API call to Balena cloud and return the device config variables received
        in response."""

        responses.add(
            responses.GET,
            TEST_GET_DEVICE_CONFIG_VARIABLES_URL,
            status=200,
            json={'d': TEST_VARIABLES}
        )

        bc = self.make_balena_cloud()
        bc._device_id = TEST_DEVICE_ID

        assert bc.get_device_config_variables() == TEST_VARIABLES

    @responses.activate
    def test_get_device_config_variables_connection_error(self):
        """Should make an API call to Balena cloud and raise `RuntimeError` due to API connection
        problem."""

        responses.add(
            responses.GET,
            TEST_GET_DEVICE_CONFIG_VARIABLES_URL,
            body=ConnectionError('Unable to connect')
        )

        bc = self.make_balena_cloud()
        bc._device_id = TEST_DEVICE_ID

        with self.assertRaises(RuntimeError) as exp:
            bc.get_device_config_variables()

        assert str(exp.exception).startswith('Failed to retrieve device config variables')

    @responses.activate
    def test_get_device_config_variables_connection_timeout(self):
        """Should make an API call to Balena cloud and raise `RuntimeError` due to API connection
        timeout."""

        responses.add(
            responses.GET,
            TEST_GET_DEVICE_CONFIG_VARIABLES_URL,
            body=ConnectTimeout(CONNECTION_EXCEPTION_MSG)
        )

        bc = self.make_balena_cloud()
        bc._device_id = TEST_DEVICE_ID

        with self.assertRaises(RuntimeError) as exp:
            bc.get_device_config_variables()

        assert str(exp.exception).startswith('Failed to retrieve device config variables')

    @responses.activate
    def test_get_device_config_variables_empty_response(self):
        """Should make an API call to Balena cloud and raise `RuntimeError` due to emtpy response
        from API."""

        responses.add(
            responses.GET,
            TEST_GET_DEVICE_CONFIG_VARIABLES_URL,
            body='',
            status=200
        )

        bc = self.make_balena_cloud()
        bc._device_id = TEST_DEVICE_ID

        with self.assertRaises(RuntimeError) as exp:
            bc.get_device_config_variables()

        assert str(exp.exception).startswith('Failed to retrieve device config variables')

    @responses.activate
    def test_create_device_config_variable_success_response(self):
        """Should make an API call to Balena cloud to create a device config variable from given
        arguments."""

        responses.add(
            responses.POST,
            TEST_CREATE_DEVICE_CONFIG_VARIABLE_URL,
            status=200,
            json={'device': TEST_DEVICE_ID, 'name': 'TEST_VAR_3', 'value': 'test-value-3'}
        )

        bc = self.make_balena_cloud()
        bc._device_id = TEST_DEVICE_ID

        bc.create_device_config_variable('TEST_VAR_3', 'test-value-3')

    @responses.activate
    def test_create_device_config_variable_connection_error(self):
        """Should make an API call to Balena cloud and raise `RuntimeError` due to API connection
        problem."""

        responses.add(
            responses.POST,
            TEST_CREATE_DEVICE_CONFIG_VARIABLE_URL,
            body=ConnectionError('Unable to connect')
        )

        bc = self.make_balena_cloud()
        bc._device_id = TEST_DEVICE_ID

        with self.assertRaises(RuntimeError) as exp:
            bc.create_device_config_variable('TEST_VAR_3', 'test-value-3')

        assert str(exp.exception).startswith('Failed to create device config variable')

    @responses.activate
    def test_create_device_config_variable_connection_timeout(self):
        """Should make an API call to Balena cloud and raise `RuntimeError` due to API connection
        timeout."""

        responses.add(
            responses.POST,
            TEST_CREATE_DEVICE_CONFIG_VARIABLE_URL,
            body=ConnectTimeout(CONNECTION_EXCEPTION_MSG)
        )

        bc = self.make_balena_cloud()
        bc._device_id = TEST_DEVICE_ID

        with self.assertRaises(RuntimeError) as exp:
            bc.create_device_config_variable('TEST_VAR_3', 'test-value-3')

        assert str(exp.exception).startswith('Failed to create device config variable')

    @responses.activate
    def test_create_device_config_variable_empty_response(self):
        """Should make an API call to Balena cloud and raise `RuntimeError` due to emtpy response
        from API."""

        responses.add(
            responses.POST,
            TEST_CREATE_DEVICE_CONFIG_VARIABLE_URL,
            body='',
            status=200
        )

        bc = self.make_balena_cloud()
        bc._device_id = TEST_DEVICE_ID

        with self.assertRaises(RuntimeError) as exp:
            bc.create_device_config_variable('TEST_VAR_3', 'test-value-3')

        assert str(exp.exception).startswith('Failed to create device config variable')

    @responses.activate
    def test_update_device_config_variable_success_response(self):
        """Should make an API call to Balena cloud to update a device config variable from given
        arguments."""

        responses.add(
            responses.PATCH,
            TEST_UPDATE_DEVICE_CONFIG_VARIABLE_URL,
            status=200,
            json={'value': 'test-value-3'}
        )

        bc = self.make_balena_cloud()

        bc.update_device_config_variable(TEST_VAR_ID, 'test-value-3')

    @responses.activate
    def test_update_device_config_variable_connection_error(self):
        """Should make an API call to Balena cloud and raise `RuntimeError` due to API connection
        problem."""

        responses.add(
            responses.PATCH,
            TEST_UPDATE_DEVICE_CONFIG_VARIABLE_URL,
            body=ConnectionError('Unable to connect')
        )

        bc = self.make_balena_cloud()

        with self.assertRaises(RuntimeError) as exp:
            bc.update_device_config_variable(TEST_VAR_ID, 'test-value-3')

        assert str(exp.exception).startswith('Failed to update device config variable')

    @responses.activate
    def test_update_device_config_variable_connection_timeout(self):
        """Should make an API call to Balena cloud and raise `RuntimeError` due to API connection
        timeout."""

        responses.add(
            responses.PATCH,
            TEST_UPDATE_DEVICE_CONFIG_VARIABLE_URL,
            body=ConnectTimeout(CONNECTION_EXCEPTION_MSG)
        )

        bc = self.make_balena_cloud()

        with self.assertRaises(RuntimeError) as exp:
            bc.update_device_config_variable(TEST_VAR_ID, 'test-value-3')

        assert str(exp.exception).startswith('Failed to update device config variable')

    @responses.activate
    def test_remove_device_config_variable_success_response(self):
        """Should make an API call to Balena cloud to remove a device config variable."""

        responses.add(
            responses.DELETE,
            TEST_REMOVE_DEVICE_CONFIG_VARIABLE_URL,
            status=200,
        )

        bc = self.make_balena_cloud()

        bc.remove_device_config_variable(TEST_VAR_ID)

    @responses.activate
    def test_remove_device_config_variable_connection_error(self):
        """Should make an API call to Balena cloud and raise `RuntimeError` due to API connection
        problem."""

        responses.add(
            responses.DELETE,
            TEST_REMOVE_DEVICE_CONFIG_VARIABLE_URL,
            body=ConnectionError('Unable to connect')
        )

        bc = self.make_balena_cloud()

        with self.assertRaises(RuntimeError) as exp:
            bc.remove_device_config_variable(TEST_VAR_ID)

        assert str(exp.exception).startswith('Failed to remove device config variable')

    @responses.activate
    def test_remove_device_config_variable_connection_timeout(self):
        """Should make an API call to Balena cloud and raise `RuntimeError` due to API connection
        timeout."""

        responses.add(
            responses.DELETE,
            TEST_REMOVE_DEVICE_CONFIG_VARIABLE_URL,
            body=ConnectTimeout(CONNECTION_EXCEPTION_MSG)
        )

        bc = self.make_balena_cloud()

        with self.assertRaises(RuntimeError) as exp:
            bc.remove_device_config_variable(TEST_VAR_ID)

        assert str(exp.exception).startswith('Failed to remove device config variable')
