import logging
from alembic.config import Config
from alembic import command


def run_migrations(script_location, dsn):
    logging.info('Running DB migrations in %r on %r', script_location, dsn)
    alembic_cfg = Config()
    alembic_cfg.set_main_option('script_location', script_location)
    alembic_cfg.set_main_option('sqlalchemy.url', dsn)
    command.upgrade(alembic_cfg, 'head')
