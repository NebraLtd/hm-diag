# Docker Container that runs the Nebra Diagnostics Tool

FROM arm32v6/alpine:3.12.4

WORKDIR /opt/

HEALTHCHECK \
    --interval=30s \
    --timeout=10s \
    --start-period=10s \
    --retries=10 \
  CMD wget -q -O - http://0.0.0.0:5000/initFile.txt || exit 1

# hadolint ignore=DL3018
RUN apk add --no-cache \
    python3=3.8.10-r0 \
    i2c-tools=4.1-r3 \
    usbutils=012-r1 \
    build-base \
    python3-dev \
    glib-dev \
    py3-pip=20.1.1-r0

RUN mkdir /tmp/build
COPY ./ /tmp/build
WORKDIR /tmp/build
RUN pip install --no-cache -r /tmp/build/requirements.txt
RUN python3 setup.py install
RUN rm -rf /tmp/build
ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:5000", "hw_diag:wsgi_app"]
