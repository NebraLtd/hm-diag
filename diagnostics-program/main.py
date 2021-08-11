# Nebra Diagnostics Tool
# This tool runs every minute to check a veriaty of parts on the Nebra Hotspot

# Import all of the libraries we require
import os
import json
import base64
from time import sleep
# import sentry_sdk
import dbus
import requests
import subprocess

# Import the HTML generator file,
# plus hardware definitions (added in container)
from html_generator import generate_html
from variant_definitions import variant_definitions

# Setup Sentry Diagnostics
# (Temporarily disabled until dbus warning can be ignored)

# sentry_key = os.getenv('SENTRY_DIAG')
# if(sentry_key):
#     print("Sentry Diagnostics Detected")
#     balena_id = os.getenv('BALENA_DEVICE_UUID')
#     balena_app = os.getenv('BALENA_APP_NAME')
#     sentry_sdk.init(sentry_key, environment=balena_app)
#     sentry_sdk.set_user({"id": balena_id})

# Start the diagnostics Loop

# Define variables
PACKET_FORWARDER_DIAGNOSTICS_FILE = '/var/pktfwd/diagnostics'
HELIUM_PUBLIC_KEYS = '/var/data/public_keys'


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
        raise e
    except PermissionError as e:
        raise e
    return file.readline().strip().upper()


def wait_for_file(file_path, attempts=5, timeout=5):
    """
    Helper function for to wait for
    files to appear on disk.
    """
    if not os.path.isfile(file_path):
        retries_left = attempts
        print('{} is missing. Waiting for file to appear.'.format(file_path))

        while retries_left > 0:
            print('...{} attempt(s) left'.format(retries_left))
            retries_left = retries_left - 1
            if os.path.isfile(file_path):
                break
            sleep(timeout)


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
    # return MC - MD - MH - MN - MSESH list
    param_list = []
    try:
        miner_bus = dbus.SystemBus()
        miner_object = miner_bus.get_object('com.helium.Miner', '/')
        miner_interface = dbus.Interface(miner_object, 'com.helium.Miner')
        try:
            p2pstatus = miner_interface.P2PStatus()
            param_list = [
                str(p2pstatus[0][1]),
                str(p2pstatus[2][1]),
                str(p2pstatus[4][1]),
                str(p2pstatus[3][1]),
                str(p2pstatus[1][1])
            ]
        except dbus.exceptions.DBusException:
            param_list = [
                "no",
                "",
                "0",
                "",
                "0"
            ]
    except Exception:
        param_list = [
            "no",
            "",
            "0",
            "",
            "0"
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
    result = subprocess.Popen(command.split())
    if param in result:
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


def main():
    while True:
        # Prints diag loop to help aid with debugging
        print("Diagnostics loop started...")

        # Create the dictionary to store all the data
        diagnostics = {
        }

        # Check the ECC Chip is present by running i2c detect and checking 0x60
        eccTest = os.popen('i2cdetect -y 1').read()

        if "60 --" in eccTest:
            diagnostics["ECC"] = True
        else:
            diagnostics["ECC"] = False

        # Get ethernet MAC address, if fail revert to dummy
        try:
            diagnostics["E0"] = open("/sys/class/net/eth0/address")\
                .readline().strip().upper()
        except FileNotFoundError:
            diagnostics["E0"] = "Unknown"

        # Get WiFi MAC address, if fail revert to dummy
        try:
            diagnostics["W0"] = open("/sys/class/net/wlan0/address")\
                .readline().strip().upper()
        except FileNotFoundError:
            diagnostics["W0"] = "Unknown"

        # Get Balena Name
        diagnostics["BN"] = os.getenv('BALENA_DEVICE_NAME_AT_INIT')

        # Get Balena UUID
        diagnostics["ID"] = os.getenv('BALENA_DEVICE_UUID')

        # Get Balena App
        diagnostics["BA"] = os.getenv('BALENA_APP_NAME')

        # Get Frequency
        diagnostics["FR"] = os.getenv('FREQ')

        # Get Firmware
        diagnostics["FW"] = os.getenv('FIRMWARE_VERSION')

        # Get Variant
        diagnostics["VA"] = os.getenv('VARIANT', 'Unknown')

        # Get RPi serial number
        diagnostics["RPI"] = open("/proc/cpuinfo")\
            .readlines()[-2].strip()[10:]

        # Get USB IDs to check for BT
        bt_id = os.popen('grep 0a12 /sys/bus/usb/devices/*/idVendor').read()
        if "0a12" in bt_id:
            diagnostics["BT"] = True
        else:
            diagnostics["BT"] = False

        #  And 4G / LTE Modem
        lte_id = os.popen('grep 2c7c /sys/bus/usb/devices/*/idVendor').read()
        if "2c7c" in lte_id:
            diagnostics["LTE"] = True
        else:
            diagnostics["LTE"] = False

        # LoRa Module Test
        diagnostics["LOR"] = None

        wait_for_file(PACKET_FORWARDER_DIAGNOSTICS_FILE)

        if os.path.isfile(PACKET_FORWARDER_DIAGNOSTICS_FILE):
            # The Pktfwder container creates this file
            # to pass over the status.
            with open(PACKET_FORWARDER_DIAGNOSTICS_FILE) as data:
                lora_status = data.read()
                if lora_status == "true":
                    diagnostics["LOR"] = True
                else:
                    diagnostics["LOR"] = False

        # Get the Public Key, Onboarding Key & Helium Animal Name
        diagnostics["PK"] = None
        wait_for_file(HELIUM_PUBLIC_KEYS)

        # Set defaults
        diagnostics["PK"] = 'Unknown'
        diagnostics["OK"] = 'Unknown'
        diagnostics["AN"] = 'Unknown'

        if os.path.isfile(HELIUM_PUBLIC_KEYS):
            try:
                pk_file = open(HELIUM_PUBLIC_KEYS).readline().split('"')
                diagnostics["PK"] = str(pk_file[1])
                diagnostics["OK"] = str(pk_file[3])
                diagnostics["AN"] = str(pk_file[5])
            except FileNotFoundError:
                sleep(10)

        # Get miner diagnostics
        try:
            miner_bus = dbus.SystemBus()
            miner_object = miner_bus.get_object('com.helium.Miner', '/')
            miner_interface = dbus.Interface(miner_object, 'com.helium.Miner')
            try:
                p2p_status = miner_interface.P2PStatus()
                diagnostics['MC'] = str(p2p_status[0][1])
                diagnostics['MD'] = str(p2p_status[2][1])
                diagnostics['MH'] = str(p2p_status[3][1])
                diagnostics['MN'] = str(p2p_status[2][1])
                diagnostics['MSESH'] = str(p2p_status[1][1])
            except dbus.exceptions.DBusException:
                diagnostics['MC'] = "no"
                diagnostics['MD'] = ""
                diagnostics['MH'] = "0"
                diagnostics['MN'] = ""
                diagnostics['MSESH'] = "0"
        except Exception:
            diagnostics['MC'] = "no"
            diagnostics['MD'] = ""
            diagnostics['MH'] = "0"
            diagnostics['MN'] = ""
            diagnostics['MSESH'] = "0"

        # I believe that:
        # if the NAT type is symmetric that it is counted as relayed.
        if diagnostics['MN'] == "symmetric":
            diagnostics['MR'] = True
        else:
            diagnostics['MR'] = False

        # Get the blockchain height from the Helium API
        try:
            bchR = requests.get('https://api.helium.io/v1/blocks/height')
            diagnostics['BCH'] = bchR.json()['data']['height']
        except requests.exceptions.ConnectionError:
            # Request failed, default to 1
            diagnostics['BCH'] = "1"

        # Check if the miner height
        # is within 500 blocks and if so say it's synced
        if int(diagnostics['MH']) > (int(diagnostics['BCH']) - 500):
            diagnostics['MS'] = True
        else:
            diagnostics['MS'] = False

        # Calculate a percentage for block sync
        diag_mh = int(diagnostics['MH'])
        diag_bch = int(diagnostics['BCH'])
        diagnostics['BSP'] = round(diag_mh/diag_bch*100, 3)

        # Check if the region has been set
        try:
            with open("/var/pktfwd/region", 'r') as data:
                region = data.read()
                if len(region) > 3:
                    print("Frequency: " + str(region))
                    diagnostics['RE'] = str(region).rstrip('\n')
        except FileNotFoundError:
            # No region found, put a dummy region in
            diagnostics['RE'] = "UN123"

        # Check the basics if they're fine and set an overall value
        # Basics are: ECC valid, Mac addresses aren't FF, BT Is present,
        # and LoRa hasn't failed
        if(
            diagnostics["ECC"] is True
            and diagnostics["E0"] != "Unknown"
            and diagnostics["W0"] != "Unknown"
            and diagnostics["BT"] is True and diagnostics["LOR"] is True
        ):
            diagnostics["PF"] = True
        else:
            diagnostics["PF"] = False

        # Add variant variables into diagnostics
        # These are variables from the hardware definitions file
        if diagnostics['VA'] != 'Unknown':
            variant_variables = variant_definitions[diagnostics['VA']]
        else:
            variant_variables = {
                'FRIENDLY': 'Developer Mode Mock Hotspot',
                'APPNAME': "Indoor",
                'SPIBUS': 'spidev1.2',
                'RESET': 38,
                'MAC': 'eth0',
                'STATUS': 25,
                'BUTTON': 26,
                'ECCOB': True,
                'TYPE': "Full"
            }
        diagnostics.update(variant_variables)

        # Create a JSON with a cutdown feature
        # set which was used in some production
        prod_diagnostics = {
            "VA": diagnostics['VA'],
            "FR": diagnostics['FR'],
            "E0": diagnostics['E0'],
            "RPI": diagnostics['RPI'],
            "OK": diagnostics['OK'],
            "PK": diagnostics['PK'],
            "PF": diagnostics["PF"],
            "ID": diagnostics["ID"]
        }

        # Generate an overall json
        diag_json = json.dumps(diagnostics)

        # Write the overall diagnostics data to a json file served via Nginx
        with open("/opt/html/diagnostics.json", 'w') as data:
            data.write(diag_json)

        # Write the same file to another directory shared between containers
        with open("/var/data/nebraDiagnostics.json", 'w') as data:
            data.write(diag_json)

        # Write the legacy production json to a file in base64
        prod_json = str(json.dumps(prod_diagnostics)).encode('ascii')
        prod_base64 = base64.b64encode(prod_json)

        with open("/opt/html/initFile.txt", 'w') as initFile:
            initFile.write(str(prod_base64, 'ascii'))

        # Finally write the HTML data using the generate HTML function
        with open("/opt/html/index.html", 'w') as htmlOut:
            htmlOut.write(generate_html(diagnostics))
        if diagnostics["PF"] is True:
            sleep(120)
        else:
            sleep(30)


if __name__ == "__main__":
    main()
