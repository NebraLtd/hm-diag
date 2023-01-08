from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from hw_diag.database.config import DB_URL


BASE = declarative_base()


def get_db_engine(debug=False):
    engine = create_engine(DB_URL, echo=debug)
    return engine


def get_db_session(debug=False):
    sessmaker = sessionmaker(bind=get_db_engine(debug))
    session = sessmaker()
    return session


# These imports are down here to prevent cyclic imports
# they are not used in this file but are required for
# alembic to include tables in revision generation.
from hw_diag.database.models.auth import AuthKeyValue  # noqa: E402,F401
from hw_diag.database.models.auth import AuthFailure  # noqa: E402,F401
