import subprocess
import os

from hm_pyhelper.lock_singleton import lock_ecc


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


@lock_ecc()
def config_search_param(command, param):
    """
    input:
        command: Command to execute
        param: The parameter we are looking for in the response
    return: True is exist, or False if doesn't exist
    Possible exceptions:
        TypeError: If the arguments passed to the function are not strings.
    """
    if type(command) is not str:
        raise TypeError("The command must be a string value")
    if type(param) is not str:
        raise TypeError("The param must be a string value")
    result = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    out, err = result.communicate()
    out = out.decode("UTF-8")
    if param in out:
        return True
    else:
        return False
