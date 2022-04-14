from datetime import datetime
import logging
import os
import traceback
import sentry_sdk
from datetime import timedelta

from flask import Flask
from flask_apscheduler import APScheduler
from retry import retry

from hw_diag.cache import cache
from hw_diag.tasks import perform_hw_diagnostics
from hw_diag.views.diagnostics import DIAGNOSTICS
from hw_diag.utilities.quectel import ensure_quectel_health
from hm_pyhelper.miner_param import provision_key
from sentry_sdk.integrations.flask import FlaskIntegration


DIAGNOSTICS_VERSION = os.getenv('DIAGNOSTICS_VERSION')
DSN_SENTRY = os.getenv('SENTRY_DIAG')
sentry_sdk.init(
    dsn=DSN_SENTRY,
    integrations=[FlaskIntegration()],
    release=f"diagnostics@{DIAGNOSTICS_VERSION}",
)

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
    scheduler.api_enabled = False
    scheduler.init_app(app)
    scheduler.start()

    @scheduler.task('cron', id='ship_diagnostics', minute='0')
    def run_ship_diagnostics_task():
        perform_hw_diagnostics(ship=True)

    @scheduler.task('interval', id='quectel_repeating', hours=1)
    def run_quectel_health_task():
        try:
            ensure_quectel_health()
        except Exception as e:
            logging.error(f'Unknown error encountered while trying to update Quectel modem '
                          f'for network compatibility: {e}')
            logging.error(traceback.format_exc())

    # bring first run time to run 2 minutes from now as well
    quectel_job = scheduler.get_job('quectel_repeating')
    quectel_job.modify(next_run_time=datetime.now()+timedelta(minutes=2))

    # Register Blueprints
    app.register_blueprint(DIAGNOSTICS)

    return app
