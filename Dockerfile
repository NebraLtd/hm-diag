# Docker Container that runs the Nebra Diagnostics Tool

ARG BUILD_BOARD

####################################################################################################
################################## Stage: builder ##################################################
FROM balenalib/"$BUILD_BOARD"-debian-python:bullseye-build-20221215 AS builder

ENV PYTHON_DEPENDENCIES_DIR=/opt/python-dependencies

RUN mkdir /tmp/build
COPY quectel/ /tmp/build/quectel
COPY hw_diag/ /tmp/build/hw_diag
COPY bigquery/ /tmp/build/bigquery
COPY requirements.txt /tmp/build/requirements.txt
COPY setup.py /tmp/build/setup.py
COPY MANIFEST.in /tmp/build/MANIFEST.in
WORKDIR /tmp/build

RUN \
    install_packages \
            cmake \
            build-essential \
            libdbus-glib-1-dev && \
    pip3 install --no-cache-dir --target="$PYTHON_DEPENDENCIES_DIR" .

# firehose build, the tar is obtained from  quectel.
# there is no install target in Makefile, doing manual copy
RUN tar -xf quectel/qfirehose/QFirehose_Linux_Android_V1.4.9.tar
# docker linter wants WORKDIR for changing directory
WORKDIR /tmp/build/QFirehose_Linux_Android_V1.4.9
RUN make && \
    cp QFirehose /usr/sbin/QFirehose && \
    rm -rf quectel/qfirehose

# No need to cleanup the builder

####################################################################################################
################################### Stage: runner ##################################################
FROM balenalib/"$BUILD_BOARD"-debian-python:bullseye-run-20221215 AS runner

ENV PYTHON_DEPENDENCIES_DIR=/opt/python-dependencies

RUN \
    install_packages \
        wget \
        i2c-tools \
        libdbus-1-3 \
        gpg

# Nebra uses /opt by convention
WORKDIR /opt/

# Import gpg key
COPY keys/manufacturing-key.gpg ./

# Copy packages from builder
COPY --from=builder "$PYTHON_DEPENDENCIES_DIR" "$PYTHON_DEPENDENCIES_DIR"

# copy modem flashing tool
COPY --from=builder /usr/sbin/QFirehose /usr/sbin/QFirehose

# copy firmware files
COPY --from=builder /tmp/build/quectel /quectel

# copy db migration files
COPY migrations/ /opt/migrations/migrations
COPY alembic.ini /opt/migrations/alembic.ini

# copy start admin session script
COPY start_admin_session /usr/sbin/start_admin_session

# Getting RUN layers together
RUN gpg --import manufacturing-key.gpg && \
    rm manufacturing-key.gpg && \
    chmod 700 /usr/sbin/start_admin_session && \
    mkdir -p /opt/nebra

# Copy ThingsIX Config
COPY thingsix_config.yaml /opt/thingsix/thingsix_config.yaml

# Add python dependencies to PYTHONPATH
ENV PYTHONPATH="${PYTHON_DEPENDENCIES_DIR}:${PYTHONPATH}"
ENV PATH="${PYTHON_DEPENDENCIES_DIR}/bin:${PATH}"

# Copy environment variables startup script
COPY setenv.sh /opt/nebra/setenv.sh

# Copy container startup script
COPY start_diagnostics.sh /opt/start_diagnostics.sh

ENTRYPOINT ["/opt/start_diagnostics.sh"]
