import unittest
import flask
from unittest.mock import patch, mock_open
import os

# Test cases
from hw_diag.app import get_app


class TestGetDiagnostics(unittest.TestCase):
    TEST_DATA = """Revision        : a020d3
    Serial\t\t: 00000000a3e7kg80
    Model           : Raspberry Pi 3 Model B Plus Rev 1.3 """

    def setUp(self):
        self.app = get_app('test_app')
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

    def test_get_json_output(self):
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
                        cresp = c.get(url)
                        error_str = ('Diagnostics have not yet run, '
                                     'please try again in a few minutes'
                                     )
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

    @patch.dict(os.environ, {'FIRMWARE_VERSION': '1337.13.37', 'DIAGNOSTICS_VERSION': 'aabbffe'})
    def test_version_endpoint(self):
        # Check the version json output
        resp = self.client.get('/version')
        reply = resp.json

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(reply['firmware_version'], '1337.13.37')
        self.assertEqual(reply['diagnostics_version'], 'aabbffe')
