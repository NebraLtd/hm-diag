FROM arm32v6/alpine:3.12.4

WORKDIR /opt/nebraDiagnostics/

RUN apk add --no-cache \
python3=3.8.8-r0 \
i2c-tools=4.1-r3 \
usbutils=012-r1 \
nginx=1.18.0-r1

RUN mkdir -p /run/nginx && mkdir html

COPY diagnostics-program /opt/nebraDiagnostics
COPY default.conf /etc/nginx/conf.d/default.conf
COPY bootstrap.min.css /opt/nebraDiagnostics/html/bootstrap.min.css

ENTRYPOINT ["sh", "/opt/nebraDiagnostics/startDiag.sh"]
