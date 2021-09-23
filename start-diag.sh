#!/usr/bin/env sh

. ./dbus-wait.sh

wait_for_dbus \
	&& gunicorn --bind 0.0.0.0:5000 hw_diag:wsgi_app
