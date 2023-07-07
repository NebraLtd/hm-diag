import os


def get_environment_var(diagnostics):
    # The order of the values in the lists is important!
    # It determines which value will be available for which key
    env_var = [
        'BALENA_DEVICE_NAME_AT_INIT',
        'BALENA_DEVICE_UUID',
        'BALENA_APP_NAME',
        'FREQ',
        'FIRMWARE_VERSION',
        'VARIANT',
        'FIRMWARE_SHORT_HASH',
        'DIAGNOSTICS_VERSION',
        'CONFIG_VERSION',
        'PKTFWD_VERSION',
        'GATEWAYRS_VERSION',
        'MULTIPLEXER_VERSION'
    ]
    keys = ["BN", "ID", "BA", "FR", "FW", "VA", "firmware_short_hash", "diagnotics_version",
            "config_version", "packet_forwarder_version", "gatewayrs_version", "multiplexer_version"
    ]

    for (var, key) in zip(env_var, keys):
        diagnostics[key] = os.getenv(var)

    if "MYST_VERSION" in os.environ:
        diagnostics["myst_version"] = os.getenv("MYST_VERSION")

    if "THINGSIX_VERSION" in os.environ:
        diagnostics["thingsix_version"] = os.getenv("THINGSIX_VERSION")
