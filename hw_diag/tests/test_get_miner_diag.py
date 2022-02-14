import unittest

from unittest.mock import patch
from copy import deepcopy

import hm_pyhelper.miner_json_rpc.client

from hw_diag.utilities.miner import fetch_miner_data


class TestGetMinerDiag(unittest.TestCase):
    PEER_ADDR = {
        'peer_addr':
            '/p2p/11rMJrFystAT3mLEdgeeVo2opSmHuMb2RXFVYh7qfqhqt2GkPv9'
    }

    HEIGHT = {'height': 1045324}

    PEER_BOOK = [
        {
            'connection_count': 5,
            'listen_addr_count': 1,
            'name': 'wild-purple-tuna',
            'nat': 'static'
        }
    ]

    @patch.object(hm_pyhelper.miner_json_rpc.client.Client, 'get_peer_addr', return_value=PEER_ADDR)
    @patch.object(hm_pyhelper.miner_json_rpc.client.Client, 'get_peer_book',
                  return_value=deepcopy(PEER_BOOK))
    @patch.object(hm_pyhelper.miner_json_rpc.client.Client, 'get_height', return_value=HEIGHT)
    def test_fetch_miner_data_valid(self, mock_height, mock_book, mock_addr):
        expected_data = {
            'MC': True,
            'MD': True,
            'MH': 1045324,
            'MN': 'static',
            'MR': False
        }

        result = fetch_miner_data({})
        self.assertEqual(result, expected_data)

    @patch.object(hm_pyhelper.miner_json_rpc.client.Client, 'get_peer_addr', return_value=PEER_ADDR)
    @patch.object(hm_pyhelper.miner_json_rpc.client.Client, 'get_peer_book',
                  return_value=deepcopy(PEER_BOOK))
    @patch.object(hm_pyhelper.miner_json_rpc.client.Client, 'get_height', return_value=HEIGHT)
    def test_fetch_miner_data_relayed(self, mock_height, mock_book, mock_addr):
        mock_book.return_value[0]['nat'] = 'symmetric'

        expected_data = {
            'MC': True,
            'MD': True,
            'MH': 1045324,
            'MN': 'symmetric',
            'MR': True
        }

        result = fetch_miner_data({})
        self.assertEqual(result, expected_data)

    @patch.object(hm_pyhelper.miner_json_rpc.client.Client, 'get_peer_addr', return_value=PEER_ADDR)
    @patch.object(hm_pyhelper.miner_json_rpc.client.Client, 'get_peer_book',
                  return_value=deepcopy(PEER_BOOK))
    @patch.object(hm_pyhelper.miner_json_rpc.client.Client, 'get_height', return_value=HEIGHT)
    def test_fetch_miner_data_not_connected(self, mock_height, mock_book, mock_addr):
        mock_book.return_value[0]['connection_count'] = 0

        expected_data = {
            'MC': False,
            'MD': True,
            'MH': 1045324,
            'MN': 'static',
            'MR': False
        }

        result = fetch_miner_data({})
        self.assertEqual(result, expected_data)
