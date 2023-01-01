import logging
import os
import uuid
import traceback
from datetime import datetime
from functools import partial
from datetime import timedelta

from flask import Flask
from flask_apscheduler import APScheduler

from hm_pyhelper.logger import get_logger

from hw_diag.cache import cache
from hw_diag.tasks import perform_hw_diagnostics
from hw_diag.utilities.event_streamer import DiagEvent
from hw_diag.utilities.network_watchdog import NetworkWatchdog
from hw_diag.utilities.sentry import init_sentry
from hw_diag.views.diagnostics import DIAGNOSTICS
from hw_diag.views.auth import AUTH
from hw_diag.utilities.quectel import ensure_quectel_health

SENTRY_DSN = os.getenv('SENTRY_DIAG')
DIAGNOSTICS_VERSION = os.getenv('DIAGNOSTICS_VERSION')
BALENA_ID = os.getenv('BALENA_DEVICE_UUID')
BALENA_APP = os.getenv('BALENA_APP_NAME')
HEARTBEAT_INTERVAL_HOURS = float(os.getenv('HEARTBEAT_INTERVAL_HOURS', 24))
SHIP_DIAG_INTERVAL_HOURS = float(os.getenv('SHIP_DIAG_INTERVAL_HOURS', 1))
NETWORK_WATCHDOG_INTERVAL_HOURS = float(os.getenv('NETWORK_WATCHDOG_INTERVAL_HOURS', 1))


init_sentry(
    sentry_dsn=SENTRY_DSN,
    release=DIAGNOSTICS_VERSION,
    balena_id=BALENA_ID,
    balena_app=BALENA_APP
)

DEBUG = bool(os.getenv('DEBUG', '0'))

log = get_logger('DIAG-APP')
if DEBUG:
    # Defaults to INFO if not explicitly set.
    log.setLevel(logging.DEBUG)


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
                      trigger='interval', hours=SHIP_DIAG_INTERVAL_HOURS, jitter=300)
    scheduler.add_job(id='quectel_repeating', func=run_quectel_health_task,
                      trigger='interval', hours=1)
    scheduler.add_job(id='network_watchdog',
                      func=partial(run_network_watchdog_task, watchdog, scheduler),
                      trigger='interval', hours=NETWORK_WATCHDOG_INTERVAL_HOURS, jitter=300)
    scheduler.add_job(id='emit_heartbeat', func=partial(run_heartbeat_task, watchdog),
                      trigger='interval', hours=HEARTBEAT_INTERVAL_HOURS, jitter=300)

    # bring first run time to run 2 minutes from now as well
    quectel_job = scheduler.get_job('quectel_repeating')
    quectel_job.modify(next_run_time=datetime.now() + timedelta(minutes=2))


def get_app(name):

    app = Flask(name)
    cache.init_app(app)
    init_scheduled_tasks(app)

    # Use a random UUID for session key, this will change each time the app
    # starts, so with reboot / update etc... users will need to reauthenticate.
    app.secret_key = str(uuid.uuid4())

    # Register Blueprints
    app.register_blueprint(DIAGNOSTICS)
    app.register_blueprint(AUTH)

    return app
