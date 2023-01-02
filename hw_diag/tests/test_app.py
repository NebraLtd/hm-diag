import unittest
import os
from flask import Flask
from unittest.mock import patch
from unittest.mock import call

# Test cases
from hw_diag.app import get_app
from hw_diag.views.diagnostics import DIAGNOSTICS
from hw_diag.views.auth import AUTH


class TestGetApp(unittest.TestCase):

    def test_returns_flask_app(self):
        # Check a flask app is returned by get_app.
        app = get_app(__name__)
        self.assertIsInstance(app, Flask)

    @patch.dict(os.environ, {"BALENA_DEVICE_TYPE": "False"})
    def test_returns_flask_app_with_gateway_exception(self):
        app = get_app(__name__)
        self.assertIsInstance(app, Flask)

    @patch('flask.Flask.register_blueprint')
    def test_blueprints_registered(
            self,
            mock_register_blueprint
    ):
        # Check the blueprint is registered during app creation.
        get_app(__name__)
        # Check we call register_blueprint...
        mock_register_blueprint.assert_called()
        # and that each blueprint is loaded (DIAGNOSTICS & AUTH).
        calls = [call(DIAGNOSTICS), call(AUTH)]
        mock_register_blueprint.assert_has_calls(calls, any_order=False)

    @patch('flask_apscheduler.APScheduler')
    def test_apscheduler_invoked(
            self,
            mock_apscheduler
    ):
        # Check APScheduler object is instantiated and api_enabled attribute
        # is True.
        get_app(__name__)
        self.assertTrue(mock_apscheduler.api_enabled)
