import unittest
import flask

from hw_diag.app import get_app


class TestThingsIXView(unittest.TestCase):

    def setUp(self):
        self.app = get_app('test_app', lean_initializations=False)
        self.client = self.app.test_client()

    def test_get_thingsix_page(self):
        url = '/thingsix'
        with self.app.test_request_context(url):
            resp = flask.Response({})
            resp = self.app.process_response(resp)
            self.assertEqual(flask.request.path, url)
            self.assertIsInstance(resp, flask.Response)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.status, '200 OK')
