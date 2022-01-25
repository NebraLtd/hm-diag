import unittest
from unittest.mock import patch
from hm_pyhelper.diagnostics.diagnostics_report import DIAGNOSTICS_ERRORS_KEY, \
                                                       DIAGNOSTICS_PASSED_KEY
from hm_pyhelper.constants.shipping import DESTINATION_NAME_KEY, DESTINATION_WALLETS_KEY
from hm_pyhelper.constants.diagnostics import VARIANT_KEY, FREQUENCY_KEY, DISK_IMAGE_KEY

# Test cases
from hw_diag.app import get_app


class TestAckAddGatewayTxn(unittest.TestCase):

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
    @patch("hw_diag.diagnostics.add_gateway_txn.ack_add_gateway_txn_diagnostic.remove_destination_wallets_from_nebra_json",  # noqa: E501
           return_value=NEBRA_JSON_SUCCESS)
    def test_success(self, nebra_json_mock, remove_nebra_json_mock):
        # Check the diagnostics JSON output.
        endpoint = '/v1/ack_add_gateway_txn'

        resp = self.client.post(endpoint)
        self.assertEqual(resp.status_code, 200)

        expected_payload = {
            DIAGNOSTICS_PASSED_KEY: True,
            DIAGNOSTICS_ERRORS_KEY: [],
        }
        self.assertDictEqual(resp.json, expected_payload)
        self.assertEqual(
            resp.headers.get('Content-Type'),
            'application/json'
        )

    @patch("hw_diag.diagnostics.add_gateway_txn.base_add_gateway_txn_diagnostic.get_nebra_json",
           return_value=NEBRA_JSON_SUCCESS)
    @patch("hw_diag.diagnostics.add_gateway_txn.ack_add_gateway_txn_diagnostic.remove_destination_wallets_from_nebra_json",  # noqa: E501
           side_effect=Exception('Cannot remove'))
    def test_failure(self, nebra_json_mock, remove_nebra_json_mock):
        # Check the diagnostics JSON output.
        endpoint = '/v1/ack_add_gateway_txn'

        resp = self.client.post(endpoint)
        self.assertEqual(resp.status_code, 406)

        expected_payload = {
            DIAGNOSTICS_PASSED_KEY: False,
            DIAGNOSTICS_ERRORS_KEY: [DESTINATION_WALLETS_KEY,
                                     DESTINATION_WALLETS_KEY],
            DESTINATION_WALLETS_KEY: "Cannot remove"
        }
        self.assertDictEqual(resp.json, expected_payload)
        self.assertEqual(
            resp.headers.get('Content-Type'),
            'application/json'
        )
