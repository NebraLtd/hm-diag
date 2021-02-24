#!/usr/bin/env bash

#Run diag
rm /opt/nebraDiagnostics/html/index.html
rm /opt/nebraDiagnostics/html/initFile.txt
cp /opt/nebraDiagnostics/html/index.html.template /opt/nebraDiagnostics/html/index.html
nginx
sleep 30
rm /opt/nebraDiagnostics/html/index.html
python3 -u /opt/nebraDiagnostics/diagnosticsProgram.py
