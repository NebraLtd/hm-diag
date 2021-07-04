#!/usr/bin/env bash

#Run diag
rm -f /opt/nebraDiagnostics/html/index.html
rm -f /opt/nebraDiagnostics/html/initFile.txt

nginx
python3 -u /opt/nebraDiagnostics/main.py
