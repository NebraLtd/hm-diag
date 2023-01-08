import unittest
from sqlalchemy.engine import Engine
from sqlalchemy.orm.session import Session

# Test Candidate
from hw_diag.database import get_db_engine
from hw_diag.database import get_db_session
from hw_diag.database.config import DB_URL


class TestDatabase(unittest.TestCase):

    def test_get_engine_returns_engine(self):
        db_engine = get_db_engine()
        self.assertIsInstance(db_engine, Engine)

    def test_get_engine_called_with_DBURL(self):
        db_engine = get_db_engine()
        self.assertEqual(str(db_engine.url), DB_URL)

    def test_get_session_returns_session(self):
        db_sess = get_db_session()
        self.assertIsInstance(db_sess, Session)
