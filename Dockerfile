# Docker Container that runs the Nebra Diagnostics Tool

####################################################################################################
################################## Stage: builder ##################################################

FROM balenalib/raspberry-pi-debian:buster-build-20211014 as builder

ENV PYTHON_DEPENDENCIES_DIR=/opt/python-dependencies

# Nebra uses /opt by convention
WORKDIR /opt/

# this installs python 3.8 which is buster default and supported by grpcio wheel
RUN \
    install_packages \
        python3-minimal \
        python3-pip \
        build-essential \
        libdbus-glib-1-dev

# updating pip to recent version otherwise it doesn't find correct grpcio
# without pinning the pip version, we get docker linter warning
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip==22.0.1 && \
    pip install --no-cache-dir --target="$PYTHON_DEPENDENCIES_DIR" -r requirements.txt

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
RUN pip --no-cache-dir  --target="$PYTHON_DEPENDENCIES_DIR" install .

# No need to cleanup the builder

####################################################################################################
################################### Stage: runner ##################################################

FROM balenalib/raspberry-pi-debian:buster-build-20211014 as runner

# libatomic is a runtime dependency for grpcio
RUN \
    install_packages \
        python3-venv \
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

# Copy packages from builder
COPY --from=builder "$PYTHON_DEPENDENCIES_DIR" "$PYTHON_DEPENDENCIES_DIR"

# copy modem flashing tool
COPY --from=builder /usr/sbin/QFirehose /usr/sbin/QFirehose

# copy firmware files
COPY --from=builder /opt/quectel /quectel

# Add python dependencies to PYTHONPATH
ENV PYTHONPATH="${PYTHON_DEPENDENCIES_DIR}:${PYTHONPATH}"
ENV PATH="${PYTHON_DEPENDENCIES_DIR}/bin:${PATH}"


ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "300", "hw_diag:wsgi_app"]
