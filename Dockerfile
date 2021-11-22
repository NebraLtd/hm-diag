# Docker Container that runs the Nebra Diagnostics Tool

####################################################################################################
################################## Stage: builder ##################################################

# The balenalib/raspberry-pi-debian-python image was tested but missed many dependencies.
FROM balenalib/raspberry-pi-debian:buster-build-20211014 as builder

RUN mkdir /tmp/build
COPY ./ /tmp/build
WORKDIR /tmp/build

# This will be the path that venv uses for installation below
ENV PATH="/opt/venv/bin:$PATH"

# Install python3-minimal, pip3, wget, venv.
# Then set venv environment copied from builder.
# Finally, use pip to install dependencies.
RUN \
    install_packages \
            python3-dev=3.7.3-1 \
            python3-minimal=3.7.3-1 \
            python3-pip=18.1-5+rpt1 \
            python3-venv=3.7.3-1 \
            libgirepository1.0-dev=1.58.3-2 \
            gcc=4:8.3.0-1+rpi2 \
            pkg-config=0.29-6 \
            libdbus-1-dev && \
    # Because the PATH is already updated above, this command creates a new venv AND activates it
    python3 -m venv /opt/venv && \
    # Given venv is active, this `pip` refers to the python3 variant
    pip install --no-cache-dir -r requirements.txt && \
    python3 setup.py install

# No need to cleanup the builder

####################################################################################################
################################### Stage: runner ##################################################

FROM balenalib/raspberry-pi-debian-python:buster-run-20211014 as runner

# Install bluez, libdbus, network-manager, python3-gi, and venv
RUN \
    install_packages \
        i2c-tools \
        bluez \
        libdbus-1-dev \
        network-manager \
        modemmanager \
        python3-venv=3.7.3-1

HEALTHCHECK \
    --interval=120s \
    --timeout=5s \
    --start-period=15s \
    --retries=10 \
  CMD wget -q -O - http://0.0.0.0:5000/initFile.txt || exit 1

# Copy venv from builder and update PATH to activate it
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:5000", "hw_diag:wsgi_app"]
