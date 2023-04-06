import unittest

from unittest.mock import patch
from unittest.mock import MagicMock

from hw_diag.utilities.thix import get_gateways
from hw_diag.utilities.thix import get_unknown_gateways
from hw_diag.utilities.thix import submit_onboard
# from hw_diag.utilities.thix import convert_h3_to_lat_lon


class OKResponse(object):
    status_code = 200
    resp_json = {}

    def __init__(self, resp_json):
        self.resp_json = resp_json

    def json(self):
        return self.resp_json


class ErrorResponse(object):
    status_code = 500
    resp_json = {}


class TestTHIXUtilities(unittest.TestCase):

    @patch('hw_diag.utilities.thix.requests')
    def test_get_gws(self, mock_requests):
        mock_requests.get = MagicMock()
        resp_json = {
          "pending": [
            {
              "localId": "0016c001f1500812",
              "networkId": "cd3b14a603d6cac3",
              "gatewayId": "0x822f1da9d3889ee8c5fcb3cc935a230e00d427ec369db8b57fa8e3f64dd92dc2"
            }
          ],
          "onboarded": [
            {
              "localId": "0016c001f1500812",
              "networkId": "cd3b14a603d6cac3",
              "gatewayId": "0x822f1da9d3889ee8c5fcb3cc935a230e00d427ec369db8b57fa8e3f64dd92dc2",
              "owner": "0xdb3082bcd200e598367ee6aa89706e82a39aa64b",
              "version": 1,
              "details": {
                "antennaGain": "3.6",
                "band": "EU868",
                "location": "8a1969ce2197fff",
                "altitude": 15
              }
            }
          ]
        }
        response = OKResponse(resp_json)
        mock_requests.get.return_value = response
        result = get_gateways()
        self.assertIsInstance(result, dict)
        self.assertEqual(result, response.resp_json)
        mock_requests.get.assert_called_with('http://thix-forwarder:8080/v1/gateways')

    @patch('hw_diag.utilities.thix.requests')
    def test_get_unknown_gws(self, mock_requests):
        mock_requests.get = MagicMock()
        resp_json = [
          {
            "localId": "0016c001f1500812",
            "firstSeen": 1675250761
          }
        ]
        response = OKResponse(resp_json)
        mock_requests.get.return_value = response
        result = get_unknown_gateways()
        self.assertIsInstance(result, list)
        self.assertEqual(result, response.resp_json)
        mock_requests.get.assert_called_with('http://thix-forwarder:8080/v1/gateways/unknown')

    @patch('hw_diag.utilities.thix.requests')
    def test_submit_onboard(self, mock_requests):
        mock_requests.post = MagicMock()
        gw = '0x6f189d06b71c4eb5c4170e5f29420475a1ea214b1cba19618e2eab2d25c72b3f'
        wallet = '0xc56bf5a78098115cf31de85feef41895c7b1605d'
        resp_json = {
          "gatewayId": gw,
          "owner": wallet,
          "version": 1,
          "chainId": 137,
          "localId": "0016c001f1500812",
          "networkId": "cd3b14a603d6cac3",
          "address": "0xb9362d934f73da7f06e18ba5e15ba0025ec29516",
          "onboarder": "0x904be50eb82e97c42afe49e088d44ce727f6a921",
          "gatewayOnboardSignature": "0x601398899eb2038246bb75f17d"
        }
        response = OKResponse(resp_json)
        mock_requests.post.return_value = response
        result = submit_onboard(gw, wallet)
        self.assertIsInstance(result, dict)
        self.assertEqual(result, response.resp_json)
        mock_requests.post.assert_called_with(
            'http://thix-forwarder:8080/v1/gateways/onboard',
            json={
                'localId': gw,
                'owner': wallet,
                'pushToThingsIX': True
            }
        )

    @patch('hw_diag.utilities.thix.requests')
    def test_submit_onboard_failure(self, mock_requests):
        mock_requests.post = MagicMock()
        gw = '0x6f189d06b71c4eb5c4170e5f29420475a1ea214b1cba19618e2eab2d25c72b3f'
        wallet = '0xc56bf5a78098115cf31de85feef41895c7b1605d'
        response = ErrorResponse()
        mock_requests.post.return_value = response
        error = None
        try:
            submit_onboard(gw, wallet)
        except Exception as err:
            error = err
        self.assertIsInstance(error, Exception)
        self.assertEqual(str(error), 'Invalid onboard request')
        mock_requests.post.assert_called_with(
            'http://thix-forwarder:8080/v1/gateways/onboard',
            json={
                'localId': gw,
                'owner': wallet,
                'pushToThingsIX': True
            }
        )

    '''
    2023-04-04 - Rob - Function removed in favour of using JS implementation
                       for conversions within the front end.

    def test_h3_to_latlng(self):
        location = '8a1874aeb4f7fff'
        expected_geolocation = {
            'latitude': 50.365592317652776,
            'longitude': -4.083930206429006
        }
        result = convert_h3_to_lat_lon(location)
        self.assertEqual(expected_geolocation, result)
    '''
