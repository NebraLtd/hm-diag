import unittest
from os.path import abspath, dirname, join
from unittest.mock import patch

import hm_pyhelper
from hm_pyhelper.constants.shipping import DESTINATION_ADD_GATEWAY_TXN_KEY
from hm_pyhelper.diagnostics.diagnostics_report import \
    DIAGNOSTICS_PASSED_KEY, DIAGNOSTICS_ERRORS_KEY, DiagnosticsReport
# from hm_pyhelper.gateway_grpc.exceptions import MinerMalformedAddGatewayTxn

from hw_diag.diagnostics.add_gateway_txn_diagnostic import AddGatewayTxnDiagnostic
from hw_diag.utilities.security import GnuPG


class TestAddGatewayTxnDiagnostic(unittest.TestCase):
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

    mocked_create_add_gateway_txn_result = {
        "address": "TestAddress",
        "fee": 65000,
        "owner": 1111,
        "payer": 2222,
        "staking fee": 4000000,
        "txn": "CrkBCiEBrlImpYLbJ0z0hw5b4g9isRyPrgbXs9X+RrJ4pJJc9MkS..."
    }

    GNUPG_HOME_DIR = './test_gnupg'
    TEST_PUB_KEY_FILE = 'data/test-key-pub.gpg'

    gnupg: GnuPG

    @classmethod
    def setUpClass(cls):
        cls.gnupg = GnuPG(gnupghome=cls.GNUPG_HOME_DIR)

        # Import test public key
        test_pub_key_full_path = join(dirname(dirname(abspath(__file__))), cls.TEST_PUB_KEY_FILE)
        with open(test_pub_key_full_path, 'r') as f:
            cls.gnupg.import_keys(f.read())

    @classmethod
    def tearDownClass(cls):
        cls.gnupg.cleanup()

    @patch.object(hm_pyhelper.gateway_grpc.client.GatewayClient, 'create_add_gateway_txn',
                  return_value=mocked_create_add_gateway_txn_result)
    def test_success(self, mock):
        diagnostics = [
            AddGatewayTxnDiagnostic(self.gnupg, self.shipping_destination_with_signature),
        ]
        diagnostics_report = DiagnosticsReport(diagnostics)
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: True,
            DIAGNOSTICS_ERRORS_KEY: [],
            DESTINATION_ADD_GATEWAY_TXN_KEY: {
                "address": "TestAddress",
                "fee": 65000,
                "owner": 1111,
                "payer": 2222,
                "staking fee": 4000000,
                "txn": "CrkBCiEBrlImpYLbJ0z0hw5b4g9isRyPrgbXs9X+RrJ4pJJc9MkS..."
            },
        })

    @patch.object(hm_pyhelper.gateway_grpc.client.GatewayClient, 'create_add_gateway_txn',
                  return_value=mocked_create_add_gateway_txn_result)
    def test_failure_invalid_signature(self, mock):
        shipping_destination_json_with_invalid_signature = b"""
            {
                "shipping_destination_label": "A Friendly User Name",
                "shipping_destination_wallets": [ "FF11" ]
            }
        """
        diagnostics = [
            AddGatewayTxnDiagnostic(self.gnupg, shipping_destination_json_with_invalid_signature),
        ]
        diagnostics_report = DiagnosticsReport(diagnostics)
        diagnostics_report.perform_diagnostics()

        self.assertDictEqual(diagnostics_report, {
            DIAGNOSTICS_PASSED_KEY: False,
            DIAGNOSTICS_ERRORS_KEY: [DESTINATION_ADD_GATEWAY_TXN_KEY,
                                     DESTINATION_ADD_GATEWAY_TXN_KEY],
            DESTINATION_ADD_GATEWAY_TXN_KEY: 'Verifying the payload PGP signature failed.',
        })

    # @patch.object(hm_pyhelper.gateway_grpc.client.GatewayClient, 'create_add_gateway_txn',
    #               side_effect=MinerMalformedAddGatewayTxn('Address is incorrect.'))
    # def test_failure_txn_exception(self, mock):
    #     diagnostics = [
    #         AddGatewayTxnDiagnostic(self.gnupg, self.shipping_destination_with_signature),
    #     ]
    #     diagnostics_report = DiagnosticsReport(diagnostics)
    #     diagnostics_report.perform_diagnostics()

    #     self.assertDictEqual(diagnostics_report, {
    #         DIAGNOSTICS_PASSED_KEY: False,
    #         DIAGNOSTICS_ERRORS_KEY: [DESTINATION_ADD_GATEWAY_TXN_KEY,
    #                                  DESTINATION_ADD_GATEWAY_TXN_KEY],
    #         DESTINATION_ADD_GATEWAY_TXN_KEY: 'Address is incorrect.',
    #     })
