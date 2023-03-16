import logging
import os
import uuid
import traceback
from datetime import datetime
from functools import partial
from datetime import timedelta

from flask import Flask
from flask import g
from flask_apscheduler import APScheduler

from hm_pyhelper.logger import get_logger

from hw_diag.cache import cache
from hw_diag.tasks import perform_hw_diagnostics
from hw_diag.utilities.event_streamer import DiagEvent
from hw_diag.utilities.network_watchdog import NetworkWatchdog
from hw_diag.utilities.balena_migration \
    import attempt_device_migration, unmount_boot_partition
from hw_diag.utilities.sentry import init_sentry
from hw_diag.views.diagnostics import DIAGNOSTICS
from hw_diag.views.auth import AUTH
from hw_diag.views.myst import MYST
from hw_diag.views.ttn import TTN
from hw_diag.views.thingsix import THINGSIX
from hw_diag.utilities.quectel import ensure_quectel_health
from hw_diag.database.config import DB_URL
from hw_diag.database import get_db_session
from hw_diag.database.migrations import run_migrations
from hw_diag.utilities.network import setup_hostname
from hw_diag.utilities.network import device_in_manufacturing

SENTRY_DSN = os.getenv('SENTRY_DIAG')
DIAGNOSTICS_VERSION = os.getenv('DIAGNOSTICS_VERSION')
BALENA_ID = os.getenv('BALENA_DEVICE_UUID')
BALENA_APP = os.getenv('BALENA_APP_NAME')
HEARTBEAT_INTERVAL_HOURS = float(os.getenv('HEARTBEAT_INTERVAL_HOURS', 24))
SHIP_DIAG_INTERVAL_HOURS = float(os.getenv('SHIP_DIAG_INTERVAL_HOURS', 1))
NETWORK_WATCHDOG_INTERVAL_HOURS = float(os.getenv('NETWORK_WATCHDOG_INTERVAL_HOURS', 1))
NEBRAOS_MIGRATION_INTERVAL_HOURS = float(os.getenv('NEBRAOS_MIGRATION_INTERVAL_HOURS', 24))
MIGRATION_TASK_DISABLED = os.getenv('NEBRA_CLOUD_MIGRATION_DISABLED', 'false').lower() == 'true'


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


def run_balena_migration_task():
    try:
        if MIGRATION_TASK_DISABLED:
            log.warning("nebra cloud migration task is disabled")
            return
        log.warning("running nebra cloud migration task")
        attempt_device_migration()
    except Exception as e:
        logging.error(f'Unknown error encountered while running nebra cloud migration'
                      f'task: {e}')
        logging.error(traceback.format_exc())
    # just to be safe umount the partition
    finally:
        unmount_boot_partition()


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

    scheduler.add_job(id='ship_diagnostics', func=run_ship_diagnostics_task,
                      trigger='interval', hours=SHIP_DIAG_INTERVAL_HOURS, jitter=300)

    scheduler.add_job(id='quectel_repeating', func=run_quectel_health_task,
                      trigger='interval', hours=1)

    watchdog = NetworkWatchdog()
    scheduler.add_job(id='network_watchdog',
                      func=partial(run_network_watchdog_task, watchdog, scheduler),
                      trigger='interval', hours=NETWORK_WATCHDOG_INTERVAL_HOURS, jitter=300)

    scheduler.add_job(id='emit_heartbeat', func=partial(run_heartbeat_task, watchdog),
                      trigger='interval', hours=HEARTBEAT_INTERVAL_HOURS, jitter=300)

    scheduler.add_job(id='check_nebra_cloud_migration', func=run_balena_migration_task,
                      trigger='interval', hours=NEBRAOS_MIGRATION_INTERVAL_HOURS, jitter=3600)

    # bring first run time to run 2 minutes from now as well
    quectel_job = scheduler.get_job('quectel_repeating')
    quectel_job.modify(next_run_time=datetime.now() + timedelta(minutes=2))


def get_app(name, lean_initializations=device_in_manufacturing()):

    if lean_initializations:
        logging.warning("Manufacturing Run: Lot of production initializations will be skipped")

    app = Flask(name)
    cache.init_app(app)

    if not lean_initializations:
        # Run database migrations on start...
        run_migrations('/opt/migrations/migrations', DB_URL)

        # not in manufacturing, all initialization will be performed.
        init_scheduled_tasks(app)
        setup_hostname()

        # Setup DB Session
        @app.before_request
        def pre_request():
            g.db = get_db_session()

        @app.after_request
        def post_request(resp):
            try:
                g.db.close()
            except Exception:
                pass
            return resp

        # Use a random UUID for session key, this will change each time the app
        # starts, so with reboot / update etc... users will need to reauthenticate.
        app.secret_key = str(uuid.uuid4())

        # Register Blueprints
        app.register_blueprint(AUTH)
        app.register_blueprint(MYST)
        app.register_blueprint(TTN)
        app.register_blueprint(THINGSIX)

    app.register_blueprint(DIAGNOSTICS)
    return app
