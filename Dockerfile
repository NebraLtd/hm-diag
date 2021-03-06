FROM arm64v8/alpine:edge

WORKDIR /opt/nebraDiagnostics/

RUN apk add --no-cache \
python3=3.8.7-r3 \
i2c-tools=4.2-r0 \
usbutils=013-r0 \
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

ENTRYPOINT ["sh", "/opt/nebraDiagnostics/startDiag.sh"]
