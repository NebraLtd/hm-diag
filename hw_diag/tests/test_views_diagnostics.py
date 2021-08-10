import unittest
import flask
from werkzeug.datastructures import ImmutableMultiDict


# Test cases
from hw_diag.app import get_app


class TestGetDiagnostics(unittest.TestCase):

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
        url = '/?json=true'

        # Server perspective
        with self.app.test_request_context(url):
            resp = flask.Response({})
            resp = self.app.process_response(resp)
            self.assertEqual(flask.request.path, '/')
            self.assertEqual(
                flask.request.args,
                ImmutableMultiDict([('json', 'true')])
            )
            self.assertIsInstance(resp, flask.Response)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.status, '200 OK')

        # Client perspective
        with self.app.test_client() as c:
            cresp = c.get(url)
            error_str = 'Diagnostics have not yet run, please try again in a few minutes'
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
