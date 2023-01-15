import unittest
from unittest.mock import patch
from functools import lru_cache
from os.path import abspath, dirname, join
import json
import responses
from requests.exceptions import ConnectionError, ConnectTimeout

from hw_diag.utilities.balena_supervisor import BalenaSupervisor
from hw_diag.utilities import balena_supervisor

# These test variables are global and not inside the class because they need to
# accessed as decorator arguments (where `self` is not available)
TEST_SUPERVISOR_ADDRESS = 'http://127.0.0.1'
TEST_SUPERVISOR_API_KEY = 'secret'
TEST_SUPERVISOR_DEVICE_STATUS_URL = 'http://127.0.0.1/v2/state/status?apikey=secret'
TEST_SUPERVISOR_SHUTDOWN_URL = 'http://127.0.0.1/v1/shutdown?apikey=secret'
TEST_SUPERVISOR_REBOOT_URL = 'http://127.0.0.1/v1/reboot?apikey=secret'
TEST_SUPERVISOR_PURGE_URL = 'http://127.0.0.1/v1/purge?apikey=secret'
TEST_SUPERVISOR_APP_ID = '12345'
TIMEOUT_EXCEPTION_MSG = 'supervisor API not accessible'


@lru_cache(maxsize=None)
def valid_status_json():
    json_full_path = join(dirname(abspath(__file__)), 'data/valid_device_state_response.json')
    return json.load(open(json_full_path, 'r'))


class TestBalenaSupervisor(unittest.TestCase):

    def test_creation(self):
        bs = BalenaSupervisor(
            TEST_SUPERVISOR_ADDRESS,
            TEST_SUPERVISOR_API_KEY,
            TEST_SUPERVISOR_APP_ID
        )

        assert bs.supervisor_address == TEST_SUPERVISOR_ADDRESS
        assert bs.supervisor_api_key == TEST_SUPERVISOR_API_KEY
        assert bs.app_id == TEST_SUPERVISOR_APP_ID
        assert bs.headers == {'Content-type': 'application/json'}

    @patch.dict(
        balena_supervisor.os.environ,
        {
            'BALENA_SUPERVISOR_ADDRESS': TEST_SUPERVISOR_ADDRESS,
            'BALENA_SUPERVISOR_API_KEY': TEST_SUPERVISOR_API_KEY,
            'BALENA_APP_ID': TEST_SUPERVISOR_APP_ID
        },
        clear=True
    )
    def test_creation_from_env(self):
        bs = BalenaSupervisor.new_from_env()

        assert bs.supervisor_address == TEST_SUPERVISOR_ADDRESS
        assert bs.supervisor_api_key == TEST_SUPERVISOR_API_KEY
        assert bs.app_id == TEST_SUPERVISOR_APP_ID
        assert bs.headers == {'Content-type': 'application/json'}

    @responses.activate
    def test_device_status_success_response_full(self):
        responses.add(
            responses.GET,
            TEST_SUPERVISOR_DEVICE_STATUS_URL,
            status=200,
            json=valid_status_json()
        )

        bs = BalenaSupervisor(
            TEST_SUPERVISOR_ADDRESS,
            TEST_SUPERVISOR_API_KEY,
            TEST_SUPERVISOR_APP_ID
        )
        assert bs.get_device_status() == valid_status_json()

    @responses.activate
    def test_device_status_success_response(self):
        responses.add(
            responses.GET,
            TEST_SUPERVISOR_DEVICE_STATUS_URL,
            status=200,
            json={'appState': 'applied'}
        )

        bs = BalenaSupervisor(
            TEST_SUPERVISOR_ADDRESS,
            TEST_SUPERVISOR_API_KEY,
            TEST_SUPERVISOR_APP_ID
        )
        assert bs.get_device_status('appState') == 'applied'

    @responses.activate
    def test_device_status_error_on_connection_error(self):
        responses.add(
            responses.GET,
            TEST_SUPERVISOR_DEVICE_STATUS_URL,
            body=ConnectionError('Unable to connect')
        )

        bs = BalenaSupervisor(
            TEST_SUPERVISOR_ADDRESS,
            TEST_SUPERVISOR_API_KEY,
            TEST_SUPERVISOR_APP_ID
        )

        with self.assertRaises(RuntimeError) as exp:
            bs.get_device_status('appState')

        assert str(exp.exception).startswith("Device status request failed")

    @responses.activate
    def test_device_status_error_on_connection_timeout(self):
        responses.add(
            responses.GET,
            TEST_SUPERVISOR_DEVICE_STATUS_URL,
            body=ConnectTimeout('Timout trying to make connection')
        )

        bs = BalenaSupervisor(
            TEST_SUPERVISOR_ADDRESS,
            TEST_SUPERVISOR_API_KEY,
            TEST_SUPERVISOR_APP_ID
        )

        with self.assertRaises(RuntimeError) as exp:
            bs.get_device_status('appState')

        assert str(exp.exception).startswith("Device status request failed")

    @responses.activate
    def test_device_status_empty_response(self):
        responses.add(
            responses.GET,
            TEST_SUPERVISOR_DEVICE_STATUS_URL,
            body='',
            status=200
        )

        bs = BalenaSupervisor(
            TEST_SUPERVISOR_ADDRESS,
            TEST_SUPERVISOR_API_KEY,
            TEST_SUPERVISOR_APP_ID
        )

        with self.assertRaises(RuntimeError) as exp:
            bs.get_device_status('appState')

        assert str(exp.exception).startswith("Supervisor API did not return valid json response")

    @responses.activate
    def test_shutdown_gateway_success_response(self):
        responses.add(
            responses.POST,
            TEST_SUPERVISOR_SHUTDOWN_URL,
            status=200,
            json={"Data": "OK", "Error": ""}
        )

        bs = BalenaSupervisor(
            TEST_SUPERVISOR_ADDRESS,
            TEST_SUPERVISOR_API_KEY,
            TEST_SUPERVISOR_APP_ID
        )
        resp = bs.shutdown()

        assert resp['Data'] == 'OK'

    @responses.activate
    def test_shutdown_gateway_error_on_connection_error(self):
        responses.add(
            responses.POST,
            TEST_SUPERVISOR_SHUTDOWN_URL,
            body=ConnectionError('Unable to connect.')
        )

        bs = BalenaSupervisor(
            TEST_SUPERVISOR_ADDRESS,
            TEST_SUPERVISOR_API_KEY,
            TEST_SUPERVISOR_APP_ID
        )

        with self.assertRaises(Exception) as exp:
            bs.shutdown()

        assert str(exp.exception) == TIMEOUT_EXCEPTION_MSG

    @responses.activate
    def test_shutdown_gateway_error_on_connection_timeout(self):
        responses.add(
            responses.POST,
            TEST_SUPERVISOR_SHUTDOWN_URL,
            body=ConnectTimeout('Timout trying to make connection')
        )

        bs = BalenaSupervisor(
            TEST_SUPERVISOR_ADDRESS,
            TEST_SUPERVISOR_API_KEY,
            TEST_SUPERVISOR_APP_ID
        )

        with self.assertRaises(Exception) as exp:
            bs.shutdown()

        assert str(exp.exception) == TIMEOUT_EXCEPTION_MSG

    @responses.activate
    def test_shutdown_gateway_empty_response(self):
        responses.add(
            responses.POST,
            TEST_SUPERVISOR_SHUTDOWN_URL,
            body='',
            status=200
        )

        bs = BalenaSupervisor(
            TEST_SUPERVISOR_ADDRESS,
            TEST_SUPERVISOR_API_KEY,
            TEST_SUPERVISOR_APP_ID
        )

        with self.assertRaises(Exception) as exp:
            bs.shutdown()

        assert str(exp.exception) == 'shutdown failed due to supervisor API issue'

    @responses.activate
    def test_reboot_gateway_success_response(self):
        responses.add(
            responses.POST,
            TEST_SUPERVISOR_REBOOT_URL,
            status=200,
            json={"Data": "OK", "Error": ""}
        )

        bs = BalenaSupervisor(
            TEST_SUPERVISOR_ADDRESS,
            TEST_SUPERVISOR_API_KEY,
            TEST_SUPERVISOR_APP_ID
        )
        resp = bs.reboot()

        assert resp['Data'] == 'OK'

    @responses.activate
    def test_reboot_gateway_error_on_connection_error(self):
        responses.add(
            responses.POST,
            TEST_SUPERVISOR_REBOOT_URL,
            body=ConnectionError('Unable to connect')
        )

        bs = BalenaSupervisor(
            TEST_SUPERVISOR_ADDRESS,
            TEST_SUPERVISOR_API_KEY,
            TEST_SUPERVISOR_APP_ID
        )

        with self.assertRaises(Exception) as exp:
            bs.reboot()

        assert str(exp.exception) == TIMEOUT_EXCEPTION_MSG

    @responses.activate
    def test_reboot_gateway_error_on_connection_timeout(self):
        responses.add(
            responses.POST,
            TEST_SUPERVISOR_REBOOT_URL,
            body=ConnectTimeout('Timout trying to make connection.')
        )

        bs = BalenaSupervisor(
            TEST_SUPERVISOR_ADDRESS,
            TEST_SUPERVISOR_API_KEY,
            TEST_SUPERVISOR_APP_ID
        )

        with self.assertRaises(Exception) as exp:
            bs.reboot()

        assert str(exp.exception) == TIMEOUT_EXCEPTION_MSG

    @responses.activate
    def test_reboot_gateway_empty_response(self):
        responses.add(
            responses.POST,
            TEST_SUPERVISOR_REBOOT_URL,
            body='',
            status=200
        )

        bs = BalenaSupervisor(
            TEST_SUPERVISOR_ADDRESS,
            TEST_SUPERVISOR_API_KEY,
            TEST_SUPERVISOR_APP_ID
        )

        with self.assertRaises(Exception) as exp:
            bs.reboot()

        assert str(exp.exception) == 'reboot failed due to supervisor API issue'

    @responses.activate
    def test_purge_gateway_success_response(self):
        responses.add(
            responses.POST,
            TEST_SUPERVISOR_PURGE_URL,
            status=200,
            json={"Data": "OK", "Error": ""}
        )

        bs = BalenaSupervisor(
            TEST_SUPERVISOR_ADDRESS,
            TEST_SUPERVISOR_API_KEY,
            TEST_SUPERVISOR_APP_ID
        )
        resp = bs.purge()

        assert resp['Data'] == 'OK'

    @responses.activate
    def test_purge_gateway_empty_response(self):
        responses.add(
            responses.POST,
            TEST_SUPERVISOR_PURGE_URL,
            body='',
            status=200
        )

        bs = BalenaSupervisor(
            TEST_SUPERVISOR_ADDRESS,
            TEST_SUPERVISOR_API_KEY,
            TEST_SUPERVISOR_APP_ID
        )

        with self.assertRaises(Exception) as exp:
            bs.purge()

        assert str(exp.exception) == 'Purge failed due to supervisor API issue'

    @responses.activate
    def test_purge_gateway_error_on_connection_timeout(self):
        responses.add(
            responses.POST,
            TEST_SUPERVISOR_PURGE_URL,
            body=ConnectTimeout('Timout trying to make connection.')
        )

        bs = BalenaSupervisor(
            TEST_SUPERVISOR_ADDRESS,
            TEST_SUPERVISOR_API_KEY,
            TEST_SUPERVISOR_APP_ID
        )

        with self.assertRaises(Exception) as exp:
            bs.purge()

        assert str(exp.exception) == TIMEOUT_EXCEPTION_MSG
