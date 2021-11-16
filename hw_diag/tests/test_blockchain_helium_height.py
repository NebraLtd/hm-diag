import unittest
from requests.exceptions import Timeout
from unittest.mock import patch, Mock
from requests.models import Response
import sys
import json
sys.path.append("..")
from hw_diag.utilities.blockchain import get_helium_blockchain_height # noqa


class TestHelium(unittest.TestCase):
    data = """{
            "data":
               {"height": 892185}
         }"""

    get_data = json.loads(data)
    the_response = Mock(spec=Response)
    the_response.json.return_value = get_data
    the_response.status_code = 200

    @patch('requests.get', return_value=the_response)
    def test_successful_request(self, _):
        res = get_helium_blockchain_height()
        self.assertEqual(res, 892185)

    the_response2 = Mock(spec=Response)
    the_response2.json.return_value = get_data
    the_response2.status_code = 404

    @patch('requests.get', return_value=the_response2)
    def test_unsuccessful_request(self, _):
        res = get_helium_blockchain_height()
        self.assertEqual(res, None)

    data = """{
         }"""

    get_data = json.loads(data)
    the_response = Mock(spec=Response)
    the_response.json.return_value = get_data
    the_response.status_code = 200

    @patch('requests.get', return_value=the_response)
    def test_wrong_data(self, _):
        self.assertRaises(KeyError, get_helium_blockchain_height)

    @patch(
        "requests.get",
        side_effect=Timeout("Timeout Error"))
    def test_timeout_exception(self, _):
        self.assertRaises(Timeout, get_helium_blockchain_height)
