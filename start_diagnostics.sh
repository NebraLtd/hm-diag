#! /bin/bash

# shellcheck source=/dev/null
source /opt/nebra/setenv.sh

gunicorn --bind 0.0.0.0:5000 --timeout 300 hw_diag.wsgi:wsgi_app
