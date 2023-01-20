# Docker Container that runs the Nebra Diagnostics Tool

####################################################################################################
################################## Stage: builder ##################################################

FROM balenalib/raspberry-pi-debian-python:bullseye-build-20221215 as builder

ENV PYTHON_DEPENDENCIES_DIR=/opt/python-dependencies

RUN mkdir /tmp/build
COPY ./ /tmp/build
WORKDIR /tmp/build

RUN \
    install_packages \
            build-essential \
            libdbus-glib-1-dev

RUN pip3 install --no-cache-dir --target="$PYTHON_DEPENDENCIES_DIR" .

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

FROM balenalib/raspberry-pi-debian-python:bullseye-run-20221215 as runner

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
COPY --from=builder /tmp/build/quectel /quectel

# copy db migration files
COPY --from=builder /tmp/build/migrations /opt/migrations/migrations
COPY --from=builder /tmp/build/alembic.ini /opt/migrations/alembic.ini

# copy start admin session script
COPY --from=builder /tmp/build/start_admin_session /usr/sbin/start_admin_session
RUN chmod 700 /usr/sbin/start_admin_session

# Add python dependencies to PYTHONPATH
ENV PYTHONPATH="${PYTHON_DEPENDENCIES_DIR}:${PYTHONPATH}"
ENV PATH="${PYTHON_DEPENDENCIES_DIR}/bin:${PATH}"

ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "300", "hw_diag.wsgi:wsgi_app"]
