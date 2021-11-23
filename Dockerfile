# Docker Container that runs the Nebra Diagnostics Tool

####################################################################################################
################################## Stage: builder ##################################################

# The balenalib/raspberry-pi-debian-python image was tested but missed many dependencies.
FROM balenalib/raspberry-pi-debian:buster-build-20211014 as builder

ENV PYTHON_DEPENDENCIES_DIR=/opt/python-dependencies

RUN mkdir /tmp/build
COPY ./ /tmp/build
WORKDIR /tmp/build

RUN \
    install_packages \
            python3-dev \
            python3-minimal \
            python3-pip \
            python3-setuptools \
            libgirepository1.0-dev \
            gcc \
            pkg-config \
            libdbus-1-dev && \
    pip3 install --no-cache-dir --target="$PYTHON_DEPENDENCIES_DIR" -r requirements.txt && \
    pip3 install --no-cache-dir --target="$PYTHON_DEPENDENCIES_DIR" .

# No need to cleanup the builder

####################################################################################################
################################### Stage: runner ##################################################

FROM balenalib/raspberry-pi-debian-python:buster-run-20211014 as runner

ENV PYTHON_DEPENDENCIES_DIR=/opt/python-dependencies

RUN \
    install_packages \
        i2c-tools \
        libdbus-1-3

HEALTHCHECK \
    --interval=120s \
    --timeout=5s \
    --start-period=15s \
    --retries=10 \
  CMD wget -q -O - http://0.0.0.0:5000/initFile.txt || exit 1

# Copy packages from builder
COPY --from=builder "$PYTHON_DEPENDENCIES_DIR" "$PYTHON_DEPENDENCIES_DIR"

# Add python dependencies to PYTHONPATH
ENV PYTHONPATH="${PYTHON_DEPENDENCIES_DIR}:${PYTHONPATH}"
ENV PATH="${PYTHON_DEPENDENCIES_DIR}/bin:${PATH}"

# gunicorn depends on "/usr/bin/python3"
RUN ln -s /usr/local/bin/python3 /usr/bin/python3

# Cleanup
RUN apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

#ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:5000", "hw_diag:wsgi_app"]
ENTRYPOINT ["tail", "-f", "/dev/null"]
