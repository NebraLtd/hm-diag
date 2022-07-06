import logging

import sentry_sdk
from hm_pyhelper.util.sentry import before_send_filter
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.logging import LoggingIntegration


def init_sentry(sentry_dsn, release, balena_id, balena_app):
    """
    Initialize sentry with balena_id and balena_app as tag.
    If sentry_dsn is not set, do nothing.
    """

    if not sentry_dsn:
        return

    sentry_logging = LoggingIntegration(
        level=logging.CRITICAL,
        event_level=logging.CRITICAL
    )

    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[sentry_logging, FlaskIntegration()],
        release=f"diagnostics@{release}",
        before_send=before_send_filter
    )

    sentry_sdk.set_tag("balena_id", balena_id)
    sentry_sdk.set_tag("balena_app", balena_app)
