# Docker Container that runs the Nebra Diagnostics Tool

FROM balenalib/raspberry-pi-debian-python:buster-run-20211014

WORKDIR /opt/

HEALTHCHECK \
    --interval=120s \
    --timeout=5s \
    --start-period=15s \
    --retries=10 \
  CMD wget -q -O - http://0.0.0.0:5000/initFile.txt || exit 1

RUN \
    install_packages \
      i2c-tools \
      usbutils

RUN mkdir /tmp/build
COPY ./ /tmp/build
WORKDIR /tmp/build

RUN \
    pip3 install --no-cache-dir -r /tmp/build/requirements.txt && \
    python3 setup.py install && \
    rm -rf /tmp/build

ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:7000", "hw_diag:wsgi_app"]