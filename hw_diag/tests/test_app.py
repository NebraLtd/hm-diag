import unittest
from flask import Flask
from unittest.mock import patch


# Test cases
from hw_diag.app import get_app
from hw_diag.views.diagnostics import DIAGNOSTICS


class TestGetApp(unittest.TestCase):

    def test_returns_flask_app(self):
        # Check a flask app is returned by get_app.
        app = get_app(__name__)
        self.assertIsInstance(app, Flask)

    @patch('flask.Flask.register_blueprint')
    def test_blueprints_registered(
            self,
            mock_register_blueprint
    ):
        # Check the blueprint is registered during app creation.
        get_app(__name__)
        # We should only call this once as we only have one blueprint,
        mock_register_blueprint.assert_called_once()
        # and that blueprint is DIAGNOSTICS.
        mock_register_blueprint.assert_called_with(DIAGNOSTICS)

    @patch('flask_apscheduler.APScheduler')
    def test_apscheduler_invoked(
            self,
            mock_apscheduler
    ):
        # Check APScheduler object is instantiated and api_enabled attribute
        # is True.
        get_app(__name__)
        self.assertTrue(mock_apscheduler.api_enabled)
