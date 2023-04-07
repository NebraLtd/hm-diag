import unittest
from unittest.mock import patch
import grpc
from concurrent import futures

import hm_pyhelper
from hm_pyhelper.protos import local_pb2_grpc
from hm_pyhelper.tests.test_gateway_grpc import TestData, MockServicer
from hw_diag.diagnostics.gateway_diagnostics import GatewayDiagnostics
from hm_pyhelper.diagnostics import DiagnosticsReport
from hm_pyhelper.constants import diagnostics as DIAG_CONSTS


class TestGetMinerDiag(unittest.TestCase):

    def start_mock_server(self):
        self.mock_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        local_pb2_grpc.add_apiServicer_to_server(MockServicer(), self.mock_server)
        self.mock_server.add_insecure_port(f'[::]:{TestData.server_port}')
        self.mock_server.start()

    def test_gateway_diagnostic(self):
        with patch.object(hm_pyhelper.gateway_grpc.client.GatewayClient.__init__,
                          '__defaults__', (f"localhost:{TestData.server_port}",)):
            self.start_mock_server()
            diagnostics = [
                GatewayDiagnostics()
            ]

            diagnostics_report = DiagnosticsReport(diagnostics)
            diagnostics_report.perform_diagnostics()
            expected_data = {
                DIAG_CONSTS.GATEWAY_REGION_KEY: TestData.region_name,
                DIAG_CONSTS.GATEWAY_REGION_SHORT_KEY: TestData.region_name,
                DIAG_CONSTS.GATEWAY_PUBKEY_KEY: TestData.pubkey_decoded
            }
            self.assertDictContainsSubset(expected_data, diagnostics_report)
            self.mock_server.stop(grace=0)
