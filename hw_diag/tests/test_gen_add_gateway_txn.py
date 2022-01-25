import unittest
from unittest.mock import patch
import hm_pyhelper.miner_json_rpc.client
from hm_pyhelper.diagnostics.diagnostics_report import DIAGNOSTICS_ERRORS_KEY, \
                                                       DIAGNOSTICS_PASSED_KEY
from hm_pyhelper.constants.shipping import DESTINATION_NAME_KEY, DESTINATION_WALLETS_KEY, \
                                           DESTINATION_ADD_GATEWAY_TXN_KEY
from hm_pyhelper.constants.diagnostics import VARIANT_KEY, FREQUENCY_KEY, DISK_IMAGE_KEY
from hm_pyhelper.constants.nebra import NEBRA_WALLET_ADDRESS

# Test cases
from hw_diag.app import get_app


class TestGenAddGatewayTxn(unittest.TestCase):

    def setUp(self):
        self.app = get_app('test_app')
        self.client = self.app.test_client()

    def mock_create_add_gateway_txn(self, owner_address: str, payer_address: str):
        return {
            "address": "TestAddress",
            "fee": 65000,
            "owner": owner_address,
            "payer": payer_address,
            "staking fee": 4000000,
            "txn": "CrkBCiEBrlImpYLbJ0z0hw5b4g9isRyPrgbXs9X+RrJ4pJJc9MkS..."
        }

    NEBRA_JSON_SUCCESS = {
        VARIANT_KEY: 'variant',
        FREQUENCY_KEY: 'frequency',
        DISK_IMAGE_KEY: 'disk_image',
        DESTINATION_NAME_KEY: 'destination_name',
        DESTINATION_WALLETS_KEY: ['owner_address']
    }

    @patch("hw_diag.diagnostics.add_gateway_txn.base_add_gateway_txn_diagnostic.get_nebra_json",
           return_value=NEBRA_JSON_SUCCESS)
    @patch.object(hm_pyhelper.miner_json_rpc.client.Client, 'create_add_gateway_txn',
                  mock_create_add_gateway_txn)
    def test_success(self, nebra_json_mock):
        # Check the diagnostics JSON output.
        endpoint = '/v1/gen_add_gateway_txn'

        resp = self.client.post(endpoint)
        self.assertEqual(resp.status_code, 200)

        expected_payload = {
            DIAGNOSTICS_PASSED_KEY: True,
            DIAGNOSTICS_ERRORS_KEY: [],
            DESTINATION_ADD_GATEWAY_TXN_KEY: {
                "address": "TestAddress",
                "fee": 65000,
                "owner": "owner_address",
                "payer": NEBRA_WALLET_ADDRESS,
                "staking fee": 4000000,
                "txn": "CrkBCiEBrlImpYLbJ0z0hw5b4g9isRyPrgbXs9X+RrJ4pJJc9MkS..."
            }
        }
        self.assertDictEqual(resp.json, expected_payload)
        self.assertEqual(
            resp.headers.get('Content-Type'),
            'application/json'
        )

    @patch("hw_diag.diagnostics.add_gateway_txn.base_add_gateway_txn_diagnostic.get_nebra_json",
           return_value=None)
    @patch.object(hm_pyhelper.miner_json_rpc.client.Client, 'create_add_gateway_txn',
                  mock_create_add_gateway_txn)
    def test_nebra_json_empty(self, nebra_json_mock):
        # Check the diagnostics JSON output.
        endpoint = '/v1/gen_add_gateway_txn'

        resp = self.client.post(endpoint)
        self.assertEqual(resp.status_code, 406)

        expected_payload = {
            DIAGNOSTICS_PASSED_KEY: False,
            DIAGNOSTICS_ERRORS_KEY: [DESTINATION_ADD_GATEWAY_TXN_KEY,
                                     DESTINATION_ADD_GATEWAY_TXN_KEY],
            DESTINATION_ADD_GATEWAY_TXN_KEY: "Nebra JSON could not be loaded or is empty."
        }
        self.assertDictEqual(resp.json, expected_payload)
        self.assertEqual(
            resp.headers.get('Content-Type'),
            'application/json'
        )

    NEBRA_JSON_DESTINATION_NAME_MISSING = {
        VARIANT_KEY: 'variant',
        FREQUENCY_KEY: 'frequency',
        DISK_IMAGE_KEY: 'disk_image',
        DESTINATION_WALLETS_KEY: ['owner_address']
    }

    @patch("hw_diag.diagnostics.add_gateway_txn.base_add_gateway_txn_diagnostic.get_nebra_json",
           return_value=NEBRA_JSON_DESTINATION_NAME_MISSING)
    @patch.object(hm_pyhelper.miner_json_rpc.client.Client, 'create_add_gateway_txn',
                  mock_create_add_gateway_txn)
    def test_destination_name_missing(self, nebra_json_mock):
        # Check the diagnostics JSON output.
        endpoint = '/v1/gen_add_gateway_txn'

        resp = self.client.post(endpoint)
        self.assertEqual(resp.status_code, 406)

        expected_payload = {
            DIAGNOSTICS_PASSED_KEY: False,
            DIAGNOSTICS_ERRORS_KEY: [DESTINATION_ADD_GATEWAY_TXN_KEY,
                                     DESTINATION_ADD_GATEWAY_TXN_KEY],
            DESTINATION_ADD_GATEWAY_TXN_KEY: "Destination name not found in Nebra JSON."
        }
        self.assertDictEqual(resp.json, expected_payload)
        self.assertEqual(
            resp.headers.get('Content-Type'),
            'application/json'
        )

    NEBRA_JSON_DESTINATION_WALLETS_EMPTY = {
        VARIANT_KEY: 'variant',
        FREQUENCY_KEY: 'frequency',
        DISK_IMAGE_KEY: 'disk_image',
        DESTINATION_NAME_KEY: 'destination_name',
        DESTINATION_WALLETS_KEY: []
    }

    @patch("hw_diag.diagnostics.add_gateway_txn.base_add_gateway_txn_diagnostic.get_nebra_json",
           return_value=NEBRA_JSON_DESTINATION_WALLETS_EMPTY)
    @patch.object(hm_pyhelper.miner_json_rpc.client.Client, 'create_add_gateway_txn',
                  mock_create_add_gateway_txn)
    def test_destination_wallets_empty(self, nebra_json_mock):
        # Check the diagnostics JSON output.
        endpoint = '/v1/gen_add_gateway_txn'

        resp = self.client.post(endpoint)
        self.assertEqual(resp.status_code, 406)

        expected_payload = {
            DIAGNOSTICS_PASSED_KEY: False,
            DIAGNOSTICS_ERRORS_KEY: [DESTINATION_ADD_GATEWAY_TXN_KEY,
                                     DESTINATION_ADD_GATEWAY_TXN_KEY],
            DESTINATION_ADD_GATEWAY_TXN_KEY: "Destination wallets array is empty in Nebra JSON."
        }
        self.assertDictEqual(resp.json, expected_payload)
        self.assertEqual(
            resp.headers.get('Content-Type'),
            'application/json'
        )

    NEBRA_JSON_DESTINATION_WALLETS_MISSING = {
        VARIANT_KEY: 'variant',
        FREQUENCY_KEY: 'frequency',
        DISK_IMAGE_KEY: 'disk_image',
        DESTINATION_NAME_KEY: 'destination_name'
    }

    @patch("hw_diag.diagnostics.add_gateway_txn.base_add_gateway_txn_diagnostic.get_nebra_json",
           return_value=NEBRA_JSON_DESTINATION_WALLETS_MISSING)
    @patch.object(hm_pyhelper.miner_json_rpc.client.Client, 'create_add_gateway_txn',
                  mock_create_add_gateway_txn)
    def test_destination_wallets_missing(self, nebra_json_mock):
        # Check the diagnostics JSON output.
        endpoint = '/v1/gen_add_gateway_txn'

        resp = self.client.post(endpoint)
        self.assertEqual(resp.status_code, 406)

        expected_payload = {
            DIAGNOSTICS_PASSED_KEY: False,
            DIAGNOSTICS_ERRORS_KEY: [DESTINATION_ADD_GATEWAY_TXN_KEY,
                                     DESTINATION_ADD_GATEWAY_TXN_KEY],
            DESTINATION_ADD_GATEWAY_TXN_KEY: "Destination wallets not found in Nebra JSON."
        }
        self.assertDictEqual(resp.json, expected_payload)
        self.assertEqual(
            resp.headers.get('Content-Type'),
            'application/json'
        )

    NEBRA_JSON_DESTINATION_WALLETS_INVALID = {
        VARIANT_KEY: 'variant',
        FREQUENCY_KEY: 'frequency',
        DISK_IMAGE_KEY: 'disk_image',
        DESTINATION_NAME_KEY: 'destination_name',
        DESTINATION_WALLETS_KEY: ['']
    }

    @patch("hw_diag.diagnostics.add_gateway_txn.base_add_gateway_txn_diagnostic.get_nebra_json",
           return_value=NEBRA_JSON_DESTINATION_WALLETS_INVALID)
    @patch.object(hm_pyhelper.miner_json_rpc.client.Client, 'create_add_gateway_txn',
                  mock_create_add_gateway_txn)
    def test_destination_wallets_invalid(self, nebra_json_mock):
        # Check the diagnostics JSON output.
        endpoint = '/v1/gen_add_gateway_txn'

        resp = self.client.post(endpoint)
        self.assertEqual(resp.status_code, 406)

        expected_payload = {
            DIAGNOSTICS_PASSED_KEY: False,
            DIAGNOSTICS_ERRORS_KEY: [DESTINATION_ADD_GATEWAY_TXN_KEY,
                                     DESTINATION_ADD_GATEWAY_TXN_KEY],
            DESTINATION_ADD_GATEWAY_TXN_KEY: "Wallet selected as owner is invalid ()"
        }
        self.assertDictEqual(resp.json, expected_payload)
        self.assertEqual(
            resp.headers.get('Content-Type'),
            'application/json'
        )
