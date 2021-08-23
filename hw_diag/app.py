import logging
import os

from flask import Flask
from flask_apscheduler import APScheduler

from hw_diag.tasks import perform_hw_diagnostics, attempt_to_set_up_upnp
from hw_diag.views.diagnostics import DIAGNOSTICS


DEBUG = os.getenv('DEBUG', 0)


log = logging.getLogger()
if DEBUG:
    # Defaults to INFO if not explicitly set.
    log.setLevel(logging.DEBUG)


def get_app(name):
    app = Flask(name)

    # Configure the backend scheduled tasks
    scheduler = APScheduler()
    scheduler.api_enabled = True
    scheduler.init_app(app)
    scheduler.start()

    # According to the original code we run the diagnostics
    # every 1 minutes, the frequency can be adjusted here...
    # TODO: Probably need to split this out into some conf file
    @scheduler.task('cron', id='run_diagnostics', minute='*/1')
    def run_diagnostics_task():
        perform_hw_diagnostics()

    @scheduler.task('cron', id='run_upnp_setup', minute='00')
    def run_upnp_setup_task():
        attempt_to_set_up_upnp()

    # Register Blueprints
    app.register_blueprint(DIAGNOSTICS)

    return app


def main():
    app = get_app(__name__)
    debug = bool(DEBUG)
    app.run('0.0.0.0', threaded=True, debug=debug)


if __name__ == '__main__':
    main()
