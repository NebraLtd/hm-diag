import unittest

from unittest.mock import patch

# Test Candidate
from hw_diag.database.migrations import run_migrations
from hw_diag.database.config import DB_URL


class TestDatabaseMigrations(unittest.TestCase):

    @patch('alembic.command.upgrade')
    def test_migrations_called(self, mock_alembic):
        script_location = '/opt/migrations/migrations'
        run_migrations(
            script_location,
            DB_URL
        )
        mock_alembic.assert_called_once()
