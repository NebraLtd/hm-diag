# Docker Container that runs the Nebra Diagnostics Tool

FROM arm32v6/alpine:3.12.4

WORKDIR /opt/

RUN apk add --no-cache \
    python3=3.8.10-r0 \
    i2c-tools=4.1-r3 \
    usbutils=012-r1 \
    miniupnpc=2.1.20191224-r0 \
    py3-pip=20.1.1-r0 \
    py3-certifi=2020.4.5.1-r0 \
    py3-urllib3=1.25.9-r0 \
    py3-requests=2.23.0-r0 \
    py3-dbus=1.2.16-r2 &&\
    pip install --no-cache-dir sentry-sdk==1.1.0

RUN mkdir /tmp/build
COPY ./ /tmp/build
WORKDIR /tmp/build
RUN pip install -r /tmp/build/requirements.txt
RUN python3 setup.py install
RUN rm -rf /tmp/build

ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:5000", "hw_diag:wsgi_app"]
