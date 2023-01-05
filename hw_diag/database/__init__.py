from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


BASE = declarative_base()


CONN_STR = 'sqlite:////var/data/hm_diag.db'


def get_db_engine(debug=False):
    engine = create_engine(CONN_STR, echo=debug)
    return engine


def get_db_session(debug=False):
    sessmaker = sessionmaker(bind=get_db_engine(debug))
    session = sessmaker()
    return session


# These imports are down here to prevent cyclic imports
# they are not used in this file but are required for
# alembic to include tables in revision generation.
from hw_diag.database.models.auth import AuthKeyValue  # noqa: E402,F401
