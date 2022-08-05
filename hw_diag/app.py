from datetime import datetime
import logging
import os
import traceback
from datetime import timedelta
from flask import Flask
from flask_apscheduler import APScheduler
from retry import retry
from hw_diag.cache import cache
from hw_diag.tasks import perform_hw_diagnostics
from hw_diag.utilities.event_streamer import DiagEvent
from hw_diag.utilities.network_watchdog import NetworkWatchdog
from hw_diag.utilities.sentry import init_sentry
from hw_diag.views.diagnostics import DIAGNOSTICS
from hw_diag.utilities.quectel import ensure_quectel_health
from hm_pyhelper.miner_param import provision_key
from functools import partial


SENTRY_DSN = os.getenv('SENTRY_DIAG')
DIAGNOSTICS_VERSION = os.getenv('DIAGNOSTICS_VERSION')
BALENA_ID = os.getenv('BALENA_DEVICE_UUID')
BALENA_APP = os.getenv('BALENA_APP_NAME')

init_sentry(
    sentry_dsn=SENTRY_DSN,
    release=DIAGNOSTICS_VERSION,
    balena_id=BALENA_ID,
    balena_app=BALENA_APP
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


def run_ship_diagnostics_task():
    perform_hw_diagnostics(ship=True)


def run_quectel_health_task():
    try:
        ensure_quectel_health()
    except Exception as e:
        logging.error(f'Unknown error encountered while trying to update Quectel modem '
                      f'for network compatibility: {e}')
        logging.error(traceback.format_exc())


def run_network_watchdog_task(watchdog, scheduler):
    try:
        network_state_event = watchdog.ensure_network_connection()
        if network_state_event == DiagEvent.NETWORK_DISCONNECTED:
            # accelerate the check for network connectivity
            watchdog_job = scheduler.get_job('network_watchdog')
            watchdog_job.modify(next_run_time=datetime.now() + timedelta(minutes=15))
    except Exception as e:
        logging.warning(f'Unknown error while checking the network connectivity : {e}')


def run_heartbeat_task(watchdog):
    try:
        watchdog.emit_heartbeat()
    except Exception as e:
        logging.warning(f'Unknown error while emitting heartbeat : {e}')


def init_scheduled_tasks(app) -> None:
    # Configure the backend scheduled tasks
    scheduler = APScheduler()
    scheduler.api_enabled = False
    scheduler.init_app(app)
    scheduler.start()
    watchdog = NetworkWatchdog()

    scheduler.add_job(id='ship_diagnostics', func=run_ship_diagnostics_task,
                      trigger='interval', minutes=60, jitter=300)
    scheduler.add_job(id='quectel_repeating', func=run_quectel_health_task,
                      trigger='interval', hours=1)
    scheduler.add_job(id='network_watchdog',
                      func=partial(run_network_watchdog_task, watchdog, scheduler),
                      trigger='interval', minutes=60, jitter=300)
    scheduler.add_job(id='emit_heartbeat', func=partial(run_heartbeat_task, watchdog),
                      trigger='interval', hours=24, jitter=300)

    # bring first run time to run 2 minutes from now as well
    quectel_job = scheduler.get_job('quectel_repeating')
    quectel_job.modify(next_run_time=datetime.now() + timedelta(minutes=2))


def get_app(name):
    try:
        if os.getenv('BALENA_DEVICE_TYPE', False):
            perform_key_provisioning()
    except Exception as e:
        log.error('Failed to provision key: {}'
                  .format(e))

    app = Flask(name)

    cache.init_app(app)

    init_scheduled_tasks(app)

    # Register Blueprints
    app.register_blueprint(DIAGNOSTICS)

    return app
