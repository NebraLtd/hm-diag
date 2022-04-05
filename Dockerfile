# Docker Container that runs the Nebra Diagnostics Tool

####################################################################################################
################################## Stage: builder ##################################################

FROM balenalib/raspberry-pi-debian:buster-build-20211014 as builder

# Nebra uses /opt by convention
WORKDIR /opt/

RUN \
    install_packages \
        python3-minimal=3.7.3-1 \
        python3-venv=3.7.3-1 \
        python3-pip \
        build-essential \
        libdbus-glib-1-dev

# This will be the path that venv uses for installation below
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt requirements.txt
RUN python3 -m venv /opt/venv && \
    pip install --upgrade pip && \
    pip install -r requirements.txt

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
RUN pip install .

# No need to cleanup the builder

####################################################################################################
################################### Stage: runner ##################################################

FROM balenalib/raspberry-pi-debian:buster-build-20211014 as runner

RUN \
    install_packages \
        python3-venv=3.7.3-1 \
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

COPY --from=builder /opt/start.sh /opt/start.sh

# Add python dependencies to PYTHONPATH
ENV PYTHONPATH="/opt:$PYTHONPATH"
ENV PATH="/opt/venv/bin:$PATH"

# ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "300", "hw_diag:wsgi_app"]
ENTRYPOINT ["/bin/bash", "/opt/start.sh"]
