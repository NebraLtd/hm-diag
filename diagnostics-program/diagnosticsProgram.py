# Checks basic hardware features.

import os
import json
import base64
from genHTML import generateHTML
from time import sleep

while True:
    print("Diag Loop")

    # Variables for all Checks

    diagnostics = {
    }

    # Check the ECC
    eccTest = os.popen('i2cdetect -y 1').read()

    if "60 --" in eccTest:
        diagnostics["ECC"] = True
    else:
        diagnostics["ECC"] = False

    # Get ethernet MAC address
    try:
        diagnostics["E0"] = open("/sys/class/net/eth0/address")\
            .readline().strip().upper()
    except FileNotFoundError:
        diagnostics["E0"] = "FF:FF:FF:FF:FF:FF"

    # Get wifi MAC address
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

    # Get Variant
    diagnostics["VA"] = os.getenv('VARIANT')

    # Get RPi serial number
    diagnostics["RPI"] = open("/proc/cpuinfo")\
        .readlines()[-2].strip()[10:]

    # Get USB IDs to check for BT And Modem
    btIdCheck = os.popen('grep 0a12 /sys/bus/usb/devices/*/idVendor').read()
    if "0a12" in btIdCheck:
        diagnostics["BT"] = True
    else:
        diagnostics["BT"] = False

    lteIdCheck = os.popen('grep 2c7c /sys/bus/usb/devices/*/idVendor').read()
    if "2c7c" in lteIdCheck:
        diagnostics["LTE"] = True
    else:
        diagnostics["LTE"] = False

    # LoRa Module Test
    diagnostics["LOR"] = None
    while(diagnostics["LOR"] is None):
        try:
            with open("/var/pktfwd/diagnostics") as diagOut:
                loraStatus = diagOut.read()
                if(loraStatus == "true"):
                    diagnostics["LOR"] = True
                else:
                    diagnostics["LOR"] = False
        except FileNotFoundError:
            #Packet forwarder container hasn't started
            sleep(10)

    diagnostics["PK"] = None
    while(diagnostics["PK"] is None):
        try:
            public_keys_file = open("/var/data/public_keys").readline().split('"')
            diagnostics["PK"] = str(public_keys_file[1])
            diagnostics["OK"] = str(public_keys_file[3])
            diagnostics["AN"] = str(public_keys_file[5])
        except FileNotFoundError:
            sleep(10)


    # print(diagnostics)

    # Check the basics if they're fine
    if(diagnostics["ECC"] is True and diagnostics["E0"] != "FF:FF:FF:FF:FF:FF"
            and diagnostics["W0"] != "FF:FF:FF:FF:FF:FF" and
            diagnostics["BT"] is True and diagnostics["LOR"] is True):
        diagnostics["PF"] = True
    else:
        diagnostics["PF"] = False

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

    diagJson = json.dumps(diagnostics)

    with open("/opt/nebraDiagnostics/html/diagnostics.json", 'w') as diagOut:
        diagOut.write(diagJson)

    with open("/var/data/nebraDiagnostics.json", 'w') as diagOut:
        diagOut.write(diagJson)

    prodJson = str(json.dumps(prodDiagnostics))
    prodBytes = prodJson.encode('ascii')
    prodBase64 = base64.b64encode(prodBytes)

    with open("/opt/nebraDiagnostics/html/initFile.txt", 'w') as initFile:
        initFile.write(str(prodBase64, 'ascii'))


    with open("/opt/nebraDiagnostics/html/index.html", 'w') as htmlOut:
        htmlOut.write(generateHTML(diagnostics))
    if(diagnostics["PF"] is True):
        sleep(300)
    else:
        sleep(30)
