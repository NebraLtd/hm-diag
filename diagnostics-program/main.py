# Nebra Diagnostics Tool
# This tool runs every minute to check a veriaty of parts on the Nebra Hotspot

# Import all of the libraries we require
import json
import base64
from time import sleep
# import sentry_sdk
import utils
import logging

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


def get_ethernet_addresses(diagnostics):
    # Get ethernet MAC and WIFI address
    path_to_files = [
        "/sys/class/net/eth0/address",
        "/sys/class/net/wlan0/address"
    ]
    keys = ["E0", "W0"]
    for (path, key) in zip(path_to_files, keys):
        try:
            diagnostics[key] = utils.get_mac_addr(path)
        except Exception as e:
            diagnostics[key] = None
            logging.error(e)


def get_environment_var(diagnostics):
    env_var = [
        'BALENA_DEVICE_NAME_AT_INIT',
        'BALENA_DEVICE_UUID',
        'BALENA_APP_NAME',
        'FREQ',
        'FIRMWARE_VERSION',
        'VARIANT'
    ]
    keys = ["BN", "ID", "BA", "FR", "FW", "VA"]

    for (var, key) in zip(env_var, keys):
        diagnostics[key] = utils.get_env_var(var)


def get_network_param(diagnostics):
    commands = [
        'i2cdetect -y 1',
        'grep 0a12 /sys/bus/usb/devices/*/idVendor',
        'grep 2c7c /sys/bus/usb/devices/*/idVendor'
    ]
    parameters = ["60 --", "0a12", "2c7c"]
    keys = ["ECC", "BT", "LTE"]

    for (command, param, key) in zip(commands, parameters, keys):
        try:
            diagnostics[key] = utils.config_search_param(command, param)
        except Exception as e:
            logging.error(e)


def write_public_keys_to_diag(data, diagnostics):
    if data is not None and len(data) == 3:
        keys = ["PK", "OK", "AN"]
        for (param, key) in zip(data, keys):
            diagnostics[key] = param
    else:
        logging.error(
            "The public keys from the file were obtained with an unknown error"
        )


def set_param_miner_diag(diagnostics):
    param_miner_diag = utils.get_miner_diagnostics()
    keys = ['MC', 'MD', 'MH', 'MN']
    for (param, key) in zip(param_miner_diag, keys):
        diagnostics[key] = param


def write_info_to_files(prod_diagnostics, diagnostics):
    diag_json = json.dumps(diagnostics)
    prod_json = str(json.dumps(prod_diagnostics)).encode('ascii')
    prod_base64 = base64.b64encode(prod_json)
    data_str = (str(prod_base64, 'ascii'))
    html_str = generate_html(diagnostics)
    path_list = [
        "/opt/nebraDiagnostics/html/diagnostics.json",
        "/var/data/nebraDiagnostics.json",
        "/opt/nebraDiagnostics/html/initFile.txt",
        "/opt/nebraDiagnostics/html/index.html"
    ]
    data_list = [
        diag_json,
        diag_json,
        data_str,
        html_str
    ]

    for (path, data) in zip(path_list, data_list):
        utils.writing_data(path, data)


def main():
    while True:
        # Prints diag loop to help aid with debugging
        print("Diag Loop")

        # Create the dictionary to store all the data

        diagnostics = {
        }

        # Get ethernet MAC and WIFI address
        get_ethernet_addresses(diagnostics)

        # Get Balena Name, UUID, App, Frequency, Firmware, Variant
        get_environment_var(diagnostics)

        # Get RPi serial number
        utils.get_rpi_serial(diagnostics)

        # Check the ECC Chip is present by running i2c detect and checking 0x60
        # Get USB IDs to check for BT And 4G / LTE Modem
        get_network_param(diagnostics)

        # LoRa Module Test
        diagnostics["LOR"] = utils.lora_module_test()

        # Get the Public Key, Onboarding Key & Helium Animal Name
        try:
            data = utils.get_public_keys()
        except PermissionError as e:
            data = None
            logging.error(e)

        write_public_keys_to_diag(data, diagnostics)

        # Get miner diagnostics
        set_param_miner_diag(diagnostics)

        # I believe that:
        # if the NAT type is symmetric that it is counted as relayed.
        if diagnostics['MN'] == "symmetric":
            diagnostics['MR'] = True
        else:
            diagnostics['MR'] = False

        # Get the blockchain height from the Helium API
        value = "1"
        try:
            value = utils.get_helium_blockchain_height()
        except KeyError as e:
            logging.warning(e)
        diagnostics['BCH'] = value

        # Check if the miner height
        # is within 500 blocks and if so say it's synced
        if int(diagnostics['MH']) > (int(diagnostics['BCH']) - 500):
            diagnostics['MS'] = True
        else:
            diagnostics['MS'] = False

        # Calculate a percentage for block sync
        diag_mh = int(diagnostics['MH'])
        diag_bch = int(diagnostics['BCH']) * 100
        diagnostics['BSP'] = round(diag_mh / diag_bch * 100, 3)

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
        if (
                diagnostics["ECC"] is True
                and diagnostics["E0"] is not None
                and diagnostics["W0"] is not None
                and diagnostics["BT"] is True and diagnostics["LOR"] is True
        ):
            diagnostics["PF"] = True
        else:
            diagnostics["PF"] = False

        # Add variant variables into diagnostics
        # These are variables from the hardware definitions file
        try:
            variant_variables = variant_definitions[diagnostics['VA']]
            diagnostics.update(variant_variables)
        except KeyError:
            pass

        # Create a json with a cutdown feature
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

        # Write the overall diagnostics data to a json file served via Nginx
        # Write the same file to another directory shared between containers
        # Write the legacy production json to a file in base64
        # Finally write the HTML data using the generate HTML function
        write_info_to_files(prod_diagnostics, diagnostics)

        if diagnostics["PF"] is True:
            sleep(120)
        else:
            sleep(30)


if __name__ == "__main__":
    main()
