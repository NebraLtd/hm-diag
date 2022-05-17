import unittest
from unittest.mock import patch

import responses
from requests.exceptions import ConnectionError, ConnectTimeout

from hw_diag.utilities.balena_supervisor import BalenaSupervisor
from hw_diag.utilities import balena_supervisor


class TestBalenaSupervisor(unittest.TestCase):

    def test_creation(self):
        bs = BalenaSupervisor('http://127.0.0.1', 'secret')

        assert bs.supervisor_address == 'http://127.0.0.1'
        assert bs.supervisor_api_key == 'secret'
        assert bs.headers == {'Content-type': 'application/json'}

    @patch.dict(
        balena_supervisor.os.environ,
        {
          'BALENA_SUPERVISOR_ADDRESS': 'http://127.0.0.1',
          'BALENA_SUPERVISOR_API_KEY': 'secret'
        },
        clear=True
    )
    def test_creation_from_env(self):
        bs = BalenaSupervisor.new_from_env()

        assert bs.supervisor_address == 'http://127.0.0.1'
        assert bs.supervisor_api_key == 'secret'
        assert bs.headers == {'Content-type': 'application/json'}

    @responses.activate
    def test_device_status_success_response(self):
        responses.add(
            responses.GET,
            'http://127.0.0.1/v2/state/status?apikey=secret',
            status=200,
            json={'appState': 'applied'}
        )

        bs = BalenaSupervisor('http://127.0.0.1', 'secret')
        assert bs.get_device_status('appState') == 'applied'

    @responses.activate
    def test_device_status_error_on_connection_error(self):
        responses.add(
            responses.GET,
            'http://127.0.0.1/v2/state/status?apikey=secret',
            body=ConnectionError('Unable to connect')
        )

        bs = BalenaSupervisor('http://127.0.0.1', 'secret')

        with self.assertRaises(Exception) as exp:
            bs.get_device_status('appState')

        assert str(exp.exception) == "Device status request failed"

    @responses.activate
    def test_device_status_error_on_connection_timeout(self):
        responses.add(
            responses.GET,
            'http://127.0.0.1/v2/state/status?apikey=secret',
            body=ConnectTimeout('Timout trying to make connection')
        )

        bs = BalenaSupervisor('http://127.0.0.1', 'secret')

        with self.assertRaises(Exception) as exp:
            bs.get_device_status('appState')

        assert str(exp.exception) == "Device status request failed"

    @responses.activate
    def test_device_status_empty_response(self):
        responses.add(
            responses.GET,
            'http://127.0.0.1/v2/state/status?apikey=secret',
            body='',
            status=200
        )

        bs = BalenaSupervisor('http://127.0.0.1', 'secret')

        resp = bs.get_device_status('appState')
        assert resp == 'Failed due to supervisor API issue'

    @responses.activate
    def test_shutdown_gateway_success_response(self):
        responses.add(
            responses.POST,
            'http://127.0.0.1/v1/shutdown?apikey=secret',
            status=200,
            json={"Data": "OK", "Error": ""}
        )

        bs = BalenaSupervisor('http://127.0.0.1', 'secret')
        resp = bs.shutdown()

        assert resp['Data'] == 'OK'

    @responses.activate
    def test_shutdown_gateway_error_on_connection_error(self):
        responses.add(
            responses.POST,
            'http://127.0.0.1/v1/shutdown?apikey=secret',
            body=ConnectionError('Unable to connect')
        )

        bs = BalenaSupervisor('http://127.0.0.1', 'secret')

        with self.assertRaises(Exception) as exp:
            bs.shutdown()

        assert str(exp.exception) == "supervisor API not accessible"

    @responses.activate
    def test_shutdown_gateway_error_on_connection_timeout(self):
        responses.add(
            responses.POST,
            'http://127.0.0.1/v1/shutdown?apikey=secret',
            body=ConnectTimeout('Timout trying to make connection')
        )

        bs = BalenaSupervisor('http://127.0.0.1', 'secret')

        with self.assertRaises(Exception) as exp:
            bs.shutdown()

        assert str(exp.exception) == 'supervisor API not accessible'

    @responses.activate
    def test_shutdown_gateway_empty_response(self):
        responses.add(
            responses.POST,
            'http://127.0.0.1/v1/shutdown?apikey=secret',
            body='',
            status=200
        )

        bs = BalenaSupervisor('http://127.0.0.1', 'secret')

        with self.assertRaises(Exception) as exp:
            bs.shutdown()

        assert str(exp.exception) == 'shutdown failed due to supervisor API issue'
