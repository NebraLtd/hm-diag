import os
import subprocess
import dbus
import requests
from time import sleep


def get_mac_addr(path):
    """
    input: path to the file with the location of the mac address
    output: A string containing a mac address
    Possible exceptions:
        FileNotFoundError - when the file is not found
        PermissionError - in the absence of access rights to the file
        TypeError - If the function argument is not a string.
    """
    if type(path) is not str:
        raise TypeError("The path must be a string value")
    try:
        file = open(path)
    except FileNotFoundError as e:
        raise FileNotFoundError(e)
    except PermissionError as e:
        raise PermissionError(e)
    return file.readline().strip().upper()


def get_env_var(variable):
    """
    input: The string value of the environment variable.
    output: The value of the environment variable if missing return none.
    """
    res = os.getenv(variable)
    return res


# Get the blockchain height from the Helium API
def get_helium_blockchain_height():
    """
    output: return current blockchain height from the Helium API
    Possible exceptions:
    TypeError - if the key ['data']['height'] in response is not found.
    """
    result = requests.get('https://api.helium.io/v1/blocks/height')
    if result.status_code == 200:
        result = result.json()
        try:
            result = result['data']['height']
        except KeyError:
            raise KeyError(
                "Not found value from key ['data']['height'] in json"
            )
        return result
    else:
        return "1"


def get_miner_diagnostics():
    # Get miner diagnostics
    # return MC - MD - MH - MN list
    param_list = []
    try:
        miner_bus = dbus.SystemBus()
        miner_object = miner_bus.get_object('com.helium.Miner', '/')
        miner_interface = dbus.Interface(miner_object, 'com.helium.Miner')
        try:
            p2pstatus = miner_interface.P2PStatus()
            param_list = [
                str(p2pstatus[0][1]),
                str(p2pstatus[1][1]),
                str(p2pstatus[3][1]),
                str(p2pstatus[2][1])
            ]
        except dbus.exceptions.DBusException as e:
            raise dbus.exceptions.DBusException(e)
    except (Exception, dbus.exceptions.DBusException):
        param_list = [
            "no",
            "",
            "0",
            ""
        ]

    return param_list


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


def writing_data(path, data):
    """
    input:
        path - path to the file
        data - data to write to file
    Possible exceptions:
        TypeError - if the path is not str.
        FileNotFoundError - Directory does not exist in the path
        PermissionError - No file permissions
    """
    if type(path) is not str:
        raise TypeError("The path must be a string value")
    try:
        with open(path, 'w') as file:
            file.write(data)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Directory does not exist in the path: {path}"
        )
    except PermissionError as e:
        raise e


def get_rpi_serial(diagnostics):
    """
    input:
        diagnostics - dict
    Possible exceptions:
        TypeError - if the path is not str.
        FileNotFoundError - "/proc/cpuinfo" not found
        PermissionError - No file permissions

    Writes the received value to the dictionary
    """
    try:
        rpi_serial = open("/proc/cpuinfo").readlines()[-2].strip()[10:]
    except FileNotFoundError as e:
        diagnostics["RPI"] = None
        raise FileNotFoundError(e)
    except PermissionError as e:
        diagnostics["RPI"] = None
        raise PermissionError(e)

    diagnostics["RPI"] = rpi_serial


def lora_module_test():
    """
    Checks the status of the lore module.
    Returns true or false.
    """
    result = None
    while result is None:
        try:
            # The Pktfwder container creates this file
            # to pass over the status.
            with open("/var/pktfwd/diagnostics") as data:
                lora_status = data.read()
                if lora_status == "true":
                    result = True
                else:
                    result = False
        except FileNotFoundError:
            # Packet forwarder container hasn't started
            sleep(10)

    return result


def get_public_keys():
    """
    get three public keys
    PK - The public key of the miner
    OK - The Onboarding key of the miner
    AN - The Animal Name of the miner
    from file "/var/data/public_keys"
    A list of keys will be returned.
    """
    pk_file = None
    while pk_file is None:
        try:
            pk_file = open("/var/data/public_keys").readline().split('"')[1::2]
        except FileNotFoundError:
            sleep(10)
        except PermissionError:
            raise PermissionError(
                "/var/data/public_keys no permission to read the file"
            )

    return pk_file
