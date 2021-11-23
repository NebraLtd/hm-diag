# Docker Container that runs the Nebra Diagnostics Tool

####################################################################################################
################################## Stage: builder ##################################################

# The balenalib/raspberry-pi-debian-python image was tested but missed many dependencies.
FROM balenalib/raspberry-pi-debian:buster-build-20211014 as builder

RUN mkdir /tmp/build
COPY ./ /tmp/build
WORKDIR /tmp/build

ENV PATH="/root/.local/bin:$PATH"

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
    pip3 install --no-cache-dir --user -r requirements.txt && \
    pip3 install --no-cache-dir --user .

# No need to cleanup the builder

####################################################################################################
################################### Stage: runner ##################################################

FROM balenalib/raspberry-pi-debian-python:buster-run-20211014 as runner

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

# Copy packages from builder and update PATH to activate it
COPY --from=builder /root/.local /root/.local
ENV PATH="/root/.local/bin:$PATH"

ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:5000", "hw_diag:wsgi_app"]
