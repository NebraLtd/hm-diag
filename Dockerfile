# Docker Container that runs the Nebra Diagnostics Tool

ARG SYSTEM_TIMEZONE=Europe/London

FROM balenalib/raspberry-pi-debian-python:buster-run-20210705

ARG SYSTEM_TIMEZONE

WORKDIR /opt/

HEALTHCHECK \
    --interval=120s \
    --timeout=5s \
    --start-period=15s \
    --retries=10 \
  CMD wget -q -O - http://0.0.0.0:5000/initFile.txt || exit 1

# hadolint ignore=DL3008
RUN \
    apt-get update && \
    DEBIAN_FRONTEND="noninteractive" \
    TZ="$SYSTEM_TIMEZONE" \
    apt-get install -y \
      i2c-tools \
      usbutils \
      --no-install-recommends && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir /tmp/build
COPY ./ /tmp/build
WORKDIR /tmp/build

RUN \
    pip3 install --no-cache-dir -r /tmp/build/requirements.txt && \
    python3 setup.py install && \
    rm -rf /tmp/build

ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:5000", "hw_diag:wsgi_app"]
