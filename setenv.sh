#!/bin/bash

base_path="/var/nebra/envvars"

# Create necessary folder if it doesn't exist
if [ ! -d $base_path ]; then
    mkdir -p $base_path
fi

create_file_if_not_exists() {
    local name="$1"
    local contents="$2"
    local fullpath="${base_path}/${name}"

    if [ ! -f "${fullpath}" ]; then
        echo "${name} parameter file doesn't exist. Setting it as ${contents} now.";
        echo "${contents}" > "${fullpath}"
    fi
}

export_param_if_not_exists() {
    local name="$1"
    local fullpath="${base_path}/${name}"

    if [ -f "${fullpath}" ]; then
        contents=$(<"${fullpath}");
        export "${name}"="${contents}"
        echo "${name} is set as ${contents}.";
    else
        echo "Error: Cannot set ${name} variable.";
    fi
}

#FREQ
if [ -z ${FREQ+x} ]; then
    export_param_if_not_exists FREQ
else
    echo "FREQ variable is already set as ${FREQ}.";
    create_file_if_not_exists FREQ "${FREQ}"
fi

#VARIANT
if [ -z ${VARIANT+x} ]; then
    export_param_if_not_exists VARIANT
else
    echo "VARIANT variable is already set as ${VARIANT}.";
    create_file_if_not_exists VARIANT "${VARIANT}"
fi
