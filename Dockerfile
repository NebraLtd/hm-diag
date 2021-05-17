# Docker Container that runs the Nebra Diagnostics Tool

FROM arm32v6/alpine:3.12.4

WORKDIR /opt/nebraDiagnostics/

RUN apk add --no-cache \
python3=3.8.10-r0 \
i2c-tools=4.1-r3 \
usbutils=012-r1 \
nginx=1.18.0-r1 \
py3-pip=20.1.1-r0 \
py3-certifi=2020.4.5.1-r0 \
py3-urllib3=1.25.9-r0 && \
pip install --no-cache-dir sentry-sdk==1.1.0 && \
apk del py3-pip

RUN mkdir -p /run/nginx && mkdir html

COPY diagnostics-program /opt/nebraDiagnostics
COPY default.conf /etc/nginx/conf.d/default.conf
COPY bootstrap.min.css /opt/nebraDiagnostics/html/bootstrap.min.css

RUN wget "https://raw.githubusercontent.com/NebraLtd/helium-hardware-definitions/master/variant_definitions.py"

ENTRYPOINT ["sh", "/opt/nebraDiagnostics/startDiag.sh"]
