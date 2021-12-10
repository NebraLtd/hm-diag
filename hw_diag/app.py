import logging
import os

from flask import Flask
from flask_apscheduler import APScheduler
from retry import retry

from hw_diag.cache import cache
from hw_diag.tasks import perform_hw_diagnostics
from hw_diag.views.diagnostics import DIAGNOSTICS
from hm_pyhelper.miner_param import provision_key


DEBUG = bool(os.getenv('DEBUG', '0'))

log = logging.getLogger()
if DEBUG:
    # Defaults to INFO if not explicitly set.
    log.setLevel(logging.DEBUG)


@retry(ValueError, tries=10, delay=1, backoff=2, logger=log)
def perform_key_provisioning():
    if not provision_key():
        raise ValueError


def get_app(name):
    try:
        if os.getenv('BALENA_DEVICE_TYPE', False):
            perform_key_provisioning()
    except Exception as e:
        log.error('Failed to provision key: {}'
                  .format(e))

    app = Flask(name)

    cache.init_app(app)

    # Configure the backend scheduled tasks
    scheduler = APScheduler()
    scheduler.api_enabled = True
    scheduler.init_app(app)
    scheduler.start()

    @scheduler.task('cron', id='ship_diagnostics', minute='0')
    def run_ship_diagnostics_task():
        perform_hw_diagnostics(ship=True)

    # Register Blueprints
    app.register_blueprint(DIAGNOSTICS)

    return app
