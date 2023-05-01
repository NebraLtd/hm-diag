#! /bin/bash

# shellcheck source=/dev/null
source /opt/nebra/setenv.sh

# fix date if too old
year=$(date +%Y)

if [ "$year" -lt 2023 ]
then
    echo "Warning: Date too old, updating"
    date -s "2 JAN 2023 18:00:00"
fi

prevent_start="${PREVENT_START_DIAG:-0}"
if [ "$prevent_start" = 1 ]; then
    echo "diagnostic app will not be started. PREVENT_START_DIAG=1"
    while true; do sleep 1000; done
fi

gunicorn --bind 0.0.0.0:80 --timeout 300 hw_diag.wsgi:wsgi_app
