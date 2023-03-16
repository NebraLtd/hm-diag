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

gunicorn --bind 0.0.0.0:80 --timeout 300 hw_diag.wsgi:wsgi_app
