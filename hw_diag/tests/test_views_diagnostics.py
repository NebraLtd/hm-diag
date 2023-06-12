import unittest
import flask
import os
from unittest.mock import patch, mock_open
from os.path import abspath, dirname, join

import hm_pyhelper
from hm_pyhelper.constants.shipping import DESTINATION_ADD_GATEWAY_TXN_KEY
from hm_pyhelper.diagnostics.diagnostics_report import DIAGNOSTICS_PASSED_KEY, \
    DIAGNOSTICS_ERRORS_KEY
from hw_diag.app import get_app
from hw_diag.utilities.security import GnuPG

@patch.dict(
        os.environ,
        {
            'BALENA_APP_ID': '123456',
            'BALENA_APP_NAME': 'Test',
        },
        clear=True
    )
class TestGetDiagnostics(unittest.TestCase):
    TEST_DATA = """Revision        : a020d3
    Serial\t\t: 00000000a3e7kg80
    Model           : Raspberry Pi 3 Model B Plus Rev 1.3 """

    GNUPG_HOME_DIR = './test_gnupg'
    TEST_PUB_KEY_FILE = 'data/test-key-pub.gpg'

    gnupg: GnuPG

    @classmethod
    def setUpClass(cls):
        cls.gnupg = GnuPG(gnupghome=cls.GNUPG_HOME_DIR)

        # Import test public key
        test_pub_key_full_path = join(dirname(abspath(__file__)), cls.TEST_PUB_KEY_FILE)
        with open(test_pub_key_full_path, 'r') as f:
            cls.gnupg.import_keys(f.read())

    @classmethod
    def tearDownClass(cls):
        cls.gnupg.cleanup()

    def setUp(self):
        self.app = get_app('test_app', lean_initializations=False)
        self.client = self.app.test_client()

    def test_get_diagnostics(self):
        # Check the diagnostics page.
        url = '/'
        with self.app.test_request_context(url):
            resp = flask.Response({})
            resp = self.app.process_response(resp)
            self.assertEqual(flask.request.path, url)
            self.assertIsInstance(resp, flask.Response)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.status, '200 OK')

    @patch('hm_pyhelper.miner_param.get_mac_address', return_value='A0:32:23:B4:C5:D6')
    def test_get_json_output(self, mock_get_mac_address):
        # Check the diagnostics JSON output.
        url = '/json'
        # Server perspective
        with self.app.test_request_context(url):
            resp = flask.Response({})
            resp = self.app.process_response(resp)
            self.assertEqual(flask.request.path, '/json')
            self.assertIsInstance(resp, flask.Response)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.status, '200 OK')

            # Client perspective
            m = mock_open(read_data='/proc/cpuinfo'.join(self.TEST_DATA))
            with patch('builtins.open', m):
                s = mock_open(read_data='diagnostic_data.json')
                with patch('builtins.open', s):
                    s.side_effect = FileNotFoundError
                    with self.app.test_client() as c:
                        with c.session_transaction() as session:
                            session['logged_in'] = True
                        cresp = c.get(url)
                        error_str = ('Diagnostics have not yet run, '
                                     'please try again in a few minutes')
                        expected = {'error': error_str}
                        self.assertEqual(cresp.json, expected)
                        self.assertEqual(
                            cresp.headers.get('Content-Type'),
                            'application/json'
                        )

    def test_initFile_output(self):
        # Check the diagnostics JSON output.
        url = '/initFile.txt'

        with self.app.test_request_context(url):
            resp = flask.Response({})
            resp = self.app.process_response(resp)
            self.assertEqual(flask.request.path, url)
            self.assertIsInstance(resp, flask.Response)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.status, '200 OK')

    @patch.dict(
        os.environ,
        {
            'FIRMWARE_VERSION': '1337.13.37',
            'DIAGNOSTICS_VERSION': 'aabbffe',
            'FIRMWARE_SHORT_HASH': '0011223'
        }
    )
    def test_version_endpoint(self):
        # Check the version json output
        resp = self.client.get('/version')
        reply = resp.json

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(reply['firmware_version'], '1337.13.37')
        self.assertEqual(reply['diagnostics_version'], 'aabbffe')
        self.assertEqual(reply['firmware_short_hash'], '0011223')

    shipping_destination_with_signature = b"""
-----BEGIN PGP SIGNED MESSAGE-----
Hash: SHA512

{
    "shipping_destination_label": "A Friendly User Name",
    "shipping_destination_wallets": [
      "FF11",
      "FF22",
      "FF33"
    ]
  }
-----BEGIN PGP SIGNATURE-----

iQGzBAEBCgAdFiEEjQFNqN85E3nZLkj+zY47EL+/pwsFAmIM9g4ACgkQzY47EL+/
pwuN0AwAiXA39VQpS5b2izZD7ia8WbEKW7wVSSwvhEVd7AFH8PfLvD8xMAbtYOwq
v4aqza9iLe31QQfWvFyfgHUOAA2bisf2M5vBpX2J74JKCSmwmpuYFRQG6vYhdlN2
mvgNswfn2YvrMD0onuaK2lyukovVWsoIBdv9RWb5fbRwx/2WzrY8otzto9XnUzNV
pkKJVcQiKHreHMnlVWaKStU4FncuBhwGO/J/cVlFqt6Gvr6UEX+9c6RztSVYDi6N
Xp5W8pZkuesrgyzxsbVKev10azqJOSbBOV007GqpT0SZt7nnIMWmXLIpcTv8Jujo
gXbipTyMB1U2KVrHD/squOeLADzErUZDwTKbNTaJfaDq2RyQdhseqnB6hLzcbv18
PEuCkSidfLzdg8e9Y6yh8I6qh5qjQnu8iM9zIzl0VHLvaNKdtjjmakLWhJ3wH6HL
ABvw+4aiz1EPX1Hmy+g/wGhIy8/wjKNcs6sGUBsoxd6ihiGg/Qzy5IzoecRvD/eW
bsoB7mtn
=Dmrt
-----END PGP SIGNATURE-----
"""

    @patch('hw_diag.diagnostics.add_gateway_txn_diagnostic.AddGatewayTxnDiagnostic.perform_test')
    def test_add_gateway_txn_endpoint_success(self, mock):
        endpoint = '/v1/add-gateway-txn'
        resp = self.client.post(endpoint,
                                data=self.shipping_destination_with_signature.decode('utf8'))

        self.assertEqual(resp.status_code, 200)
        self.assertDictEqual(resp.json, {
            DIAGNOSTICS_PASSED_KEY: True,
            DIAGNOSTICS_ERRORS_KEY: []
        })

    mocked_create_add_gateway_txn_result = {
        "address": "TestAddress",
        "fee": 65000,
        "owner": 1111,
        "payer": 2222,
        "staking fee": 4000000,
        "txn": "CrkBCiEBrlImpYLbJ0z0hw5b4g9isRyPrgbXs9X+RrJ4pJJc9MkS..."
    }

    @patch.object(hm_pyhelper.gateway_grpc.client.GatewayClient, 'create_add_gateway_txn',
                  return_value=mocked_create_add_gateway_txn_result)
    @patch('hw_diag.views.diagnostics.GnuPG')
    def test_add_gateway_txn_success(self, mock_gnupg, mock_txn):
        mock_gnupg.return_value = self.gnupg

        endpoint = '/v1/add-gateway-txn'
        resp = self.client.post(endpoint,
                                data=self.shipping_destination_with_signature.decode('utf8'))

        self.assertEqual(resp.status_code, 200)
        self.assertDictEqual(resp.json, {
            DIAGNOSTICS_PASSED_KEY: True,
            DIAGNOSTICS_ERRORS_KEY: [],
            DESTINATION_ADD_GATEWAY_TXN_KEY: self.mocked_create_add_gateway_txn_result,
        })

    @patch.object(hm_pyhelper.gateway_grpc.client.GatewayClient, 'create_add_gateway_txn',
                  return_value=mocked_create_add_gateway_txn_result)
    @patch('hw_diag.views.diagnostics.GnuPG')
    def test_add_gateway_txn_failure_no_payload(self, mock_gnupg, mock_txn):
        mock_gnupg.return_value = self.gnupg

        endpoint = '/v1/add-gateway-txn'
        resp = self.client.post(endpoint, data=None)

        self.assertEqual(resp.status_code, 406)
        self.assertDictEqual(resp.json, {
            DIAGNOSTICS_PASSED_KEY: False,
            DIAGNOSTICS_ERRORS_KEY: [DESTINATION_ADD_GATEWAY_TXN_KEY,
                                     DESTINATION_ADD_GATEWAY_TXN_KEY],
            DESTINATION_ADD_GATEWAY_TXN_KEY: 'Can not find payload.',
        })

    @patch.object(hm_pyhelper.gateway_grpc.client.GatewayClient, 'create_add_gateway_txn',
                  return_value=mocked_create_add_gateway_txn_result)
    @patch('hw_diag.views.diagnostics.GnuPG')
    def test_add_gateway_txn_failure_invalid_signature(self, mock_gnupg, mock_txn):
        mock_gnupg.return_value = self.gnupg

        endpoint = '/v1/add-gateway-txn'
        resp = self.client.post(endpoint, data='a payload with invalid signature')

        self.assertEqual(resp.status_code, 500)
        self.assertDictEqual(resp.json, {
            DIAGNOSTICS_PASSED_KEY: False,
            DIAGNOSTICS_ERRORS_KEY: [DESTINATION_ADD_GATEWAY_TXN_KEY,
                                     DESTINATION_ADD_GATEWAY_TXN_KEY],
            DESTINATION_ADD_GATEWAY_TXN_KEY: 'Verifying the payload PGP signature failed.',
        })
