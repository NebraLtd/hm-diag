import unittest
import os
from flask import Flask
from unittest.mock import patch
from unittest.mock import call

# Test cases
from hw_diag.app import get_app
from hw_diag.views.diagnostics import DIAGNOSTICS
from hw_diag.views.auth import AUTH
from hw_diag.views.myst import MYST
from hw_diag.views.thingsix import THINGSIX
from hw_diag.views.ttn import TTN
from hw_diag.views.backup_restore import BACKUP_RESTORE
from hw_diag.views.wingbits import WINGBITS


class TestGetApp(unittest.TestCase):

    @patch('alembic.command.upgrade')
    def test_returns_flask_app(self, mock_alembic):
        # Check a flask app is returned by get_app.
        app = get_app(__name__)
        self.assertIsInstance(app, Flask)

    @patch.dict(os.environ, {"BALENA_DEVICE_TYPE": "False"})
    @patch('alembic.command.upgrade')
    def test_returns_flask_app_with_gateway_exception(self, mock_alembic):
        app = get_app(__name__)
        self.assertIsInstance(app, Flask)

    @patch('flask.Flask.register_blueprint')
    @patch('alembic.command.upgrade')
    def test_blueprints_registered(
            self,
            mock_alembic,
            mock_register_blueprint
    ):
        # Check the blueprint is registered during app creation.
        get_app(__name__, lean_initializations=False)
        # Check we call register_blueprint...
        mock_register_blueprint.assert_called()
        # and that each blueprint is loaded (DIAGNOSTICS & AUTH).
        calls = [
            call(AUTH),
            call(MYST),
            call(TTN),
            call(THINGSIX),
            call(BACKUP_RESTORE),
            call(DIAGNOSTICS),
            call(WINGBITS)
        ]
        mock_register_blueprint.assert_has_calls(calls, any_order=True)

    @patch('flask_apscheduler.APScheduler')
    @patch('alembic.command.upgrade')
    def test_apscheduler_invoked(
            self,
            mock_alembic,
            mock_apscheduler
    ):
        # Check APScheduler object is instantiated and api_enabled attribute
        # is True.
        get_app(__name__)
        self.assertTrue(mock_apscheduler.api_enabled)
