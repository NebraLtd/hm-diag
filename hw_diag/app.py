import logging
import os

from flask import Flask
from flask_apscheduler import APScheduler

from hw_diag.tasks import perform_hw_diagnostics
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
    @scheduler.task(
        'cron',
        id='run_diagnostics',
        minute='5,10,15,20,25,30,35,40,45,50,55')
    def run_diagnostics_task():
        perform_hw_diagnostics(ship=False)

    @scheduler.task('cron', id='ship_diagnostics', minute='0')
    def run_ship_diagnostics_task():
        perform_hw_diagnostics(ship=True)

    # Register Blueprints
    app.register_blueprint(DIAGNOSTICS)

    return app


def main():
    app = get_app(__name__)
    debug = bool(DEBUG)
    app.run('0.0.0.0', threaded=True, debug=debug)


if __name__ == '__main__':
    main()
