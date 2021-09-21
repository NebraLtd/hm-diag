import unittest

from unittest.mock import patch
from unittest.mock import MagicMock
from copy import deepcopy

from hw_diag.utilities.miner import fetch_miner_data


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

class TestGetMinerDiag(unittest.TestCase):

    @patch('hw_diag.utilities.miner.client')
    def test_fetch_miner_data_valid(self, mock_client):
        mock_client.get_peer_addr = MagicMock()
        mock_client.get_peer_addr.return_value = PEER_ADDR
        mock_client.get_peer_book = MagicMock()
        mock_client.get_height = MagicMock()
        mock_client.get_height.return_value = HEIGHT
        mock_client.get_peer_book.return_value = deepcopy(PEER_BOOK)

        expected_data = {
            'AN': 'wild-purple-tuna',
            'MC': True,
            'MD': True,
            'MH': 1045324,
            'MN': 'static',
            'MR': False,
            'OK': '11rMJrFystAT3mLEdgeeVo2opSmHuMb2RXFVYh7qfqhqt2GkPv9',
            'PK': '11rMJrFystAT3mLEdgeeVo2opSmHuMb2RXFVYh7qfqhqt2GkPv9'
        }

        result = fetch_miner_data({})
        self.assertEqual(result, expected_data)

    @patch('hw_diag.utilities.miner.client')
    def test_fetch_miner_data_relayed(self, mock_client):
        mock_client.get_peer_addr = MagicMock()
        mock_client.get_peer_addr.return_value = PEER_ADDR
        mock_client.get_peer_book = MagicMock()
        mock_client.get_height = MagicMock()
        mock_client.get_height.return_value = HEIGHT
        mock_client.get_peer_book.return_value = deepcopy(PEER_BOOK)
        mock_client.get_peer_book.return_value[0]['nat'] = 'symmetric'

        expected_data = {
            'AN': 'wild-purple-tuna',
            'MC': True,
            'MD': True,
            'MH': 1045324,
            'MN': 'symmetric',
            'MR': True,
            'OK': '11rMJrFystAT3mLEdgeeVo2opSmHuMb2RXFVYh7qfqhqt2GkPv9',
            'PK': '11rMJrFystAT3mLEdgeeVo2opSmHuMb2RXFVYh7qfqhqt2GkPv9'
        }

        result = fetch_miner_data({})
        self.assertEqual(result, expected_data)

    @patch('hw_diag.utilities.miner.client')
    def test_fetch_miner_data_not_connected(self, mock_client):
        mock_client.get_peer_addr = MagicMock()
        mock_client.get_peer_addr.return_value = PEER_ADDR
        mock_client.get_peer_book = MagicMock()
        mock_client.get_height = MagicMock()
        mock_client.get_height.return_value = HEIGHT
        mock_client.get_peer_book.return_value = deepcopy(PEER_BOOK)
        mock_client.get_peer_book.return_value[0]['connection_count'] = 0

        expected_data = {
            'AN': 'wild-purple-tuna',
            'MC': False,
            'MD': True,
            'MH': 1045324,
            'MN': 'static',
            'MR': False,
            'OK': '11rMJrFystAT3mLEdgeeVo2opSmHuMb2RXFVYh7qfqhqt2GkPv9',
            'PK': '11rMJrFystAT3mLEdgeeVo2opSmHuMb2RXFVYh7qfqhqt2GkPv9'
        }

        result = fetch_miner_data({})
        self.assertEqual(result, expected_data)

    @patch('hw_diag.utilities.miner.client')
    def test_fetch_miner_data_not_dialable(self, mock_client):
        mock_client.get_peer_addr = MagicMock()
        mock_client.get_peer_addr.return_value = PEER_ADDR
        mock_client.get_peer_book = MagicMock()
        mock_client.get_height = MagicMock()
        mock_client.get_height.return_value = HEIGHT
        mock_client.get_peer_book.return_value = deepcopy(PEER_BOOK)
        mock_client.get_peer_book.return_value[0]['connection_count'] = 0
        mock_client.get_peer_book.return_value[0]['listen_addr_count'] = 0

        expected_data = {
            'AN': 'wild-purple-tuna',
            'MC': False,
            'MD': False,
            'MH': 1045324,
            'MN': 'static',
            'MR': False,
            'OK': '11rMJrFystAT3mLEdgeeVo2opSmHuMb2RXFVYh7qfqhqt2GkPv9',
            'PK': '11rMJrFystAT3mLEdgeeVo2opSmHuMb2RXFVYh7qfqhqt2GkPv9'
        }

        result = fetch_miner_data({})
        self.assertEqual(result, expected_data)
