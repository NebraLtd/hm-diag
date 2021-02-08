FROM arm64v8/alpine:edge

WORKDIR /opt/nebraDiagnostics/

RUN apk add --no-cache \
python3=3.8.7-r0 \
i2c-tools=4.2-r0 \
usbutils=013-r0 \
py3-qrcode=6.1-r2 \
py3-dbus=1.2.16-r2 \
nginx=1.18.0-r14

RUN mkdir -p /run/nginx
RUN mkdir html
COPY startDiag.sh startDiag.sh
COPY Ubuntu-Bold.ttf Ubuntu-Bold.ttf
COPY diagnosticsProgram.py diagnosticsProgram.py
COPY genHTML.py genHTML.py

WORKDIR /etc/nginx/conf.d
COPY default.conf default.conf

WORKDIR /opt/nebraDiagnostics/html/
COPY bootstrap.min.css bootstrap.min.css
COPY index.html.template index.html.template

RUN addgroup -r diag && adduser --no-log-init -r -g diag diag

USER diag

ENTRYPOINT ["sh", "/opt/nebraDiagnostics/startDiag.sh"]
