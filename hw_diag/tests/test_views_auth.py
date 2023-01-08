import unittest
import flask

from hw_diag.app import get_app


class TestAuthView(unittest.TestCase):

    def setUp(self):
        self.app = get_app('test_app')
        self.client = self.app.test_client()

    def test_get_login_form(self):
        url = '/login'
        with self.app.test_request_context(url):
            resp = flask.Response({})
            resp = self.app.process_response(resp)
            self.assertEqual(flask.request.path, url)
            self.assertIsInstance(resp, flask.Response)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.status, '200 OK')

    def test_get_logout(self):
        url = '/logout'
        with self.app.test_request_context(url):
            resp = flask.Response({})
            resp = self.app.process_response(resp)
            self.assertEqual(flask.request.path, url)
            self.assertIsInstance(resp, flask.Response)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.status, '200 OK')
