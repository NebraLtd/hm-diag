FROM arm32v5/alpine:edge

WORKDIR /opt/nebraDiagnostics/

RUN apk add --no-cache \
python3=3.8.7-r3 \
i2c-tools=4.2-r0 \
usbutils=013-r0 \
nginx=1.18.0-r14

RUN mkdir -p /run/nginx && mkdir html

COPY diagnostics-program /opt/nebraDiagnostics
COPY default.conf /etc/nginx/conf.d/default.conf
COPY bootstrap.min.css /opt/nebraDiagnostics/html/bootstrap.min.css

ENTRYPOINT ["sh", "/opt/nebraDiagnostics/startDiag.sh"]
