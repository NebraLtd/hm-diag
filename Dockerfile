# Docker Container that runs the Nebra Diagnostics Tool

####################################################################################################
################################## Stage: builder ##################################################

FROM balenalib/raspberry-pi-debian:buster-build-20211014 as builder

# Nebra uses /opt by convention
WORKDIR /opt/

# this installs python 3.7.3 which is buster default and supported by grpcio wheel
RUN \
    install_packages \
        python3-minimal \
        python3-venv \
        python3-pip \
        build-essential \
        libdbus-glib-1-dev

# This will be the path that venv uses for installation below
ENV PATH="/opt/venv/bin:$PATH"

# without pinning the pip version, we get linter warning
COPY requirements.txt requirements.txt
RUN python3 -m venv /opt/venv && \
    pip install --no-cache-dir --upgrade pip==22.0.1 && \
    pip install --no-cache-dir -r requirements.txt

# firehose build, the tar is obtained from  quectel.
# there is no install target in Makefile, doing manual copy
COPY quectel quectel
RUN tar -xf ./quectel/qfirehose/QFirehose_Linux_Android_V1.4.9.tar
# docker linter wants WORKDIR for changing directory
WORKDIR /opt/QFirehose_Linux_Android_V1.4.9
RUN make && \
    cp QFirehose /usr/sbin/QFirehose && \
    rm -rf quectel/qfirehose

WORKDIR /opt
COPY ./ /opt
RUN pip --no-cache-dir install .

# No need to cleanup the builder

####################################################################################################
################################### Stage: runner ##################################################

FROM balenalib/raspberry-pi-debian-python:buster-build-20211014 as runner

RUN \
    install_packages \
        wget \
        i2c-tools \
        libdbus-1-3 \
        gpg \
        libatomic1

# Nebra uses /opt by convention
WORKDIR /opt/

# Import gpg key
COPY keys/manufacturing-key.gpg ./
RUN gpg --import manufacturing-key.gpg
RUN rm manufacturing-key.gpg

# @TODO: Re-enable health-check once Balena supports it fully.
# HEALTHCHECK \
#    --interval=120s \
#    --timeout=5s \
#    --start-period=15s \
#    --retries=10 \
#  CMD wget -q -O - http://0.0.0.0:5000/initFile.txt || exit 1


# copy python env
COPY --from=builder /opt/venv /opt/venv

# copy modem flashing tool
COPY --from=builder /usr/sbin/QFirehose /usr/sbin/QFirehose

# copy firmware files
COPY --from=builder /opt/quectel /quectel

# Add python venv path
ENV PATH="/opt/venv/bin:$PATH"

ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:80", "--timeout", "300", "hw_diag:wsgi_app"]
