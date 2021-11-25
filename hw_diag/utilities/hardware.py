import logging
import os
from time import sleep

from hm_pyhelper.miner_param import get_public_keys_rust
from hm_pyhelper.hardware_definitions import variant_definitions, is_rockpi
from hw_diag.utilities.shell import config_search_param


def should_display_lte(diagnostics):
    variant = diagnostics.get('VA')
    variant_data = variant_definitions.get(variant)
    if not variant_data:
        return False
    return variant_data.get('CELLULAR')


def set_diagnostics_bt_lte(diagnostics):
    devices = [
        ['BT', '0a12'],
        ['LTE', '2c7c'],  # Quectel
        ['LTE', '68a2'],  # Sierra Wireless MC7700
        ['LTE', '1bc7'],  # Telit / Reyax
        ['LTE', '1e0e'],  # SimCom SIM7100E
        ['LTE', '12d1'],  # Huawei ME909s-120
        ['LTE', '2cd2']   # MikroTik R11e-LTE6
    ]

    for dev_type, dev_addr in devices:
        resp = os.popen(
            'grep %s /sys/bus/usb/devices/*/idVendor' % dev_addr
        ).read()
        if dev_addr in resp:
            diagnostics[dev_type] = True
        else:
            diagnostics[dev_type] = False

    return diagnostics


def detect_ecc(diagnostics):
    # The order of the values in the lists is important!
    # It determines which value will be available for which key
    if is_rockpi():
        commands = [
            'i2cdetect -y 7'
        ]
    else:
        commands = [
            'i2cdetect -y 1'
        ]

    parameters = ["60 --"]
    keys = ["ECC"]

    for (command, param, key) in zip(commands, parameters, keys):
        try:
            diagnostics[key] = config_search_param(command, param)
        except Exception as e:
            logging.error(e)


def get_serial_number(diagnostics):
    """
    input:
        diagnostics - dict
    Possible exceptions:
        TypeError - if the path is not str.
        FileNotFoundError - "/proc/device-tree/serial-number" not found
        PermissionError - No file permissions
    Writes the received value to the dictionary
    """
    try:
        serial_number = open("/proc/device-tree/serial-number").readline() \
                            .rstrip('\x00')
    except FileNotFoundError as e:
        raise e
    except PermissionError as e:
        raise e

    diagnostics["serial_number"] = serial_number


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


def get_public_keys_and_ignore_errors():
    public_keys = get_public_keys_rust()
    if not public_keys:
        error_msg = "ECC failure"
        public_keys = {
            'name': error_msg,
            'key': error_msg
        }

    return public_keys
