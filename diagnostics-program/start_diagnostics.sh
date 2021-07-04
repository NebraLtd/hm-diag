#!/usr/bin/env bash

#Run diag
rm -f /opt/html/index.html
rm -f /opt/html/initFile.txt

nginx
python3 -u /opt/main.py
