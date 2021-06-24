#!/usr/bin/env bash

#Run diag
rm -f /opt/nebraDiagnostics/html/index.html
rm -f /opt/nebraDiagnostics/html/initFile.txt
#rm -f /var/data/public_keys
#cp /opt/nebraDiagnostics/html/index.html.template /opt/nebraDiagnostics/html/index.html

nginx
#sleep 30
#rm -f /opt/nebraDiagnostics/html/index.html
python3 -u /opt/nebraDiagnostics/main.py
