import unittest
from unittest.mock import patch
import grpc
from concurrent import futures

import hm_pyhelper
from hm_pyhelper.protos import local_pb2_grpc
from hm_pyhelper.tests.test_gateway_grpc import TestData, MockServicer

from hw_diag.utilities.miner import fetch_miner_data


class TestGetMinerDiag(unittest.TestCase):

    def start_mock_server(self):
        self.mock_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        local_pb2_grpc.add_apiServicer_to_server(MockServicer(), self.mock_server)
        self.mock_server.add_insecure_port(f'[::]:{TestData.server_port}')
        self.mock_server.start()

    @patch('hm_pyhelper.gateway_grpc.client.GatewayClient.get_gateway_version',
           return_value=TestData.expected_summary['gateway_version'])
    def test_fetch_miner_data_valid(self, mock_get_gateway_version):
        with patch.object(hm_pyhelper.gateway_grpc.client.GatewayClient.__init__,
                          '__defaults__', (f"localhost:{TestData.server_port}",)):
            self.start_mock_server()
            expected_data = {
                'validator_address': TestData.validator_address_decoded,
                'validator_uri': TestData.height_res.gateway.uri,
                'block_age': TestData.height_res.block_age,
                'MH': TestData.height_res.height,
                'RE': TestData.region_name,
                'miner_key': TestData.pubkey_decoded,
                'FW': TestData.expected_summary['gateway_version']
            }

            result = fetch_miner_data({})
            print(result)
            self.assertEqual(result, expected_data)
            self.mock_server.stop(grace=0)

    def test_fetch_miner_data_not_connected(self):
        diagnostic_data = {}
        fetch_miner_data(diagnostic_data)
        self.assertEqual(diagnostic_data, {})
