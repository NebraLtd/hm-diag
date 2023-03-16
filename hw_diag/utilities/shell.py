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
        'FIRMWARE_SHORT_HASH'
    ]
    keys = ["BN", "ID", "BA", "FR", "FW", "VA", "firmware_short_hash"]

    for (var, key) in zip(env_var, keys):
        diagnostics[key] = os.getenv(var)
