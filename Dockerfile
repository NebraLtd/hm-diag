FROM balenalib/raspberry-pi-debian:buster-run

WORKDIR /opt/nebraDiagnostics/

RUN \
apt-get update && \
DEBIAN_FRONTEND="noninteractive" \
TZ="Europe/London" \
apt-get -y install \
nginx=1.14.2-2+deb10u3 \
python3-minimal=3.7.3-1 \
usbutils=1:010-3 \
i2c-tools=4.1-1 \
--no-install-recommends && \
apt-get autoremove -y &&\
apt-get clean && \
rm -rf /var/lib/apt/lists/*

RUN mkdir -p /run/nginx && mkdir html

COPY diagnostics-program /opt/nebraDiagnostics
COPY default.conf /etc/nginx/conf.d/default.conf
COPY bootstrap.min.css /opt/nebraDiagnostics/html/bootstrap.min.css

ENTRYPOINT ["sh", "/opt/nebraDiagnostics/startDiag.sh"]
