# Nebra Diagnostics Tool
# This tool runs every minute to check a veriaty of parts on the Nebra Hotspot

# Import all of the libraries we require
import os
import json
import base64
from time import sleep
import sentry_sdk
import dbus
import requests

# Import the HTML generator file, plus hardware definitions (added in container)
from html_generator import generate_html
from variant_definitions import variant_definitions

# Setup Sentry Diagnostics (Temporarily disabled until dbus warning can be ignored)

# sentry_key = os.getenv('SENTRY_DIAG')
# if(sentry_key):
#     print("Sentry Diagnostics Detected")
#     balena_id = os.getenv('BALENA_DEVICE_UUID')
#     balena_app = os.getenv('BALENA_APP_NAME')
#     sentry_sdk.init(sentry_key, environment=balena_app)
#     sentry_sdk.set_user({"id": balena_id})

# Start the diagnostics Loop

while True:
    # Prints diag loop to help aid with debugging
    print("Diag Loop")

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
        diagnostics["E0"] = "FF:FF:FF:FF:FF:FF"

    # Get WiFi MAC address, if fail revert to dummy
    try:
        diagnostics["W0"] = open("/sys/class/net/wlan0/address")\
            .readline().strip().upper()
    except FileNotFoundError:
        diagnostics["W0"] = "FF:FF:FF:FF:FF:FF"

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
    diagnostics["VA"] = os.getenv('VARIANT')

    # Get RPi serial number
    diagnostics["RPI"] = open("/proc/cpuinfo")\
        .readlines()[-2].strip()[10:]

    # Get USB IDs to check for BT
    btIdCheck = os.popen('grep 0a12 /sys/bus/usb/devices/*/idVendor').read()
    if "0a12" in btIdCheck:
        diagnostics["BT"] = True
    else:
        diagnostics["BT"] = False

    #  And 4G / LTE Modem
    lteIdCheck = os.popen('grep 2c7c /sys/bus/usb/devices/*/idVendor').read()
    if "2c7c" in lteIdCheck:
        diagnostics["LTE"] = True
    else:
        diagnostics["LTE"] = False

    # LoRa Module Test
    diagnostics["LOR"] = None
    while(diagnostics["LOR"] is None):
        try:
            # The Pktfwder container creates this file to pass over the status.
            with open("/var/pktfwd/diagnostics") as diagOut:
                loraStatus = diagOut.read()
                if(loraStatus == "true"):
                    diagnostics["LOR"] = True
                else:
                    diagnostics["LOR"] = False
        except FileNotFoundError:
            # Packet forwarder container hasn't started
            sleep(10)

    # Get the Public Key, Onboarding Key & Helium Animal Name
    diagnostics["PK"] = None
    while(diagnostics["PK"] is None):
        try:
            pk_file = open("/var/data/public_keys").readline().split('"')
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
            p2pstatus = miner_interface.P2PStatus()
            diagnostics['MC'] = str(p2pstatus[0][1])
            diagnostics['MD'] = str(p2pstatus[1][1])
            diagnostics['MH'] = str(p2pstatus[3][1])
            diagnostics['MN'] = str(p2pstatus[2][1])
        except dbus.exceptions.DBusException:
            diagnostics['MC'] = "no"
            diagnostics['MD'] = ""
            diagnostics['MH'] = "0"
            diagnostics['MN'] = ""
    except:
        diagnostics['MC'] = "no"
        diagnostics['MD'] = ""
        diagnostics['MH'] = "0"
        diagnostics['MN'] = ""

    # I believe that if the NAT type is symmetric that it is counted as relayed.
    if(diagnostics['MN'] == "symmetric"):
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

    # Check if the miner height is within 500 blocks and if so say it's synced
    if(int(diagnostics['MH']) > (int(diagnostics['BCH'])-500)):
        diagnostics['MS'] = True
    else:
        diagnostics['MS'] = False

    # Calculate a percentage for block sync
    diagnostics['BSP'] = round(((int(diagnostics['MH'])/int(diagnostics['BCH']))*100),3)

    # Check if the region has been set
    try:
        with open("/var/pktfwd/region", 'r') as regionOut:
            regionFile = regionOut.read()
            if(len(regionFile) > 3):
                print("Frequency: " + str(regionFile))
                diagnostics['RE'] = str(regionFile).rstrip('\n')
    except FileNotFoundError:
        # No region found, put a dummy region in
        diagnostics['RE'] = "UN123"

    # Check the basics if they're fine and set an overall value
    # Basics are: ECC valid, Mac addresses aren't FF, BT Is present,
    # and LoRa hasn't failed
    if(diagnostics["ECC"] is True and diagnostics["E0"] != "FF:FF:FF:FF:FF:FF"
            and diagnostics["W0"] != "FF:FF:FF:FF:FF:FF" and
            diagnostics["BT"] is True and diagnostics["LOR"] is True):
        diagnostics["PF"] = True
    else:
        diagnostics["PF"] = False

    # Add variant variables into diagnostics
    # These are variables from the hardware definitions file
    variant_variables = variant_definitions[diagnostics['VA']]
    diagnostics.update(variant_variables)

    # Create a json with a cutdown feature set which was used in some production
    prodDiagnostics = {
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
    diagJson = json.dumps(diagnostics)

    # Write the overall diagnostics data to a json file served via Nginx
    with open("/opt/nebraDiagnostics/html/diagnostics.json", 'w') as diagOut:
        diagOut.write(diagJson)

    # Write the same file to another directory shared between containers
    with open("/var/data/nebraDiagnostics.json", 'w') as diagOut:
        diagOut.write(diagJson)

    # Write the legacy production json to a file in base64
    prodJson = str(json.dumps(prodDiagnostics))
    prodBytes = prodJson.encode('ascii')
    prodBase64 = base64.b64encode(prodBytes)

    with open("/opt/nebraDiagnostics/html/initFile.txt", 'w') as initFile:
        initFile.write(str(prodBase64, 'ascii'))

    # Finally write the HTML data using the generate HTML function
    with open("/opt/nebraDiagnostics/html/index.html", 'w') as htmlOut:
        htmlOut.write(generate_html(diagnostics))
    if(diagnostics["PF"] is True):
        sleep(120)
    else:
        sleep(30)
