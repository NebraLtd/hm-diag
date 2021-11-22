import logging
from time import sleep
import dbus
from hm_pyhelper.miner_param import get_public_keys_rust
from hm_pyhelper.hardware_definitions import variant_definitions
from hw_diag.utilities.shell import config_search_param

log = logging.getLogger()
log.setLevel(logging.DEBUG)

# BlueZ dbus constants
BLUEZ_SERVICE_NAME = 'org.bluez'
DBUS_OM_IFACE = 'org.freedesktop.DBus.ObjectManager'
ADAPTER_IFACE = 'org.bluez.Adapter1'

# NetworkManager dbus constants
NM_SERVICE_NAME = 'org.freedesktop.NetworkManager'
NM_OBJECT_PATH = '/org/freedesktop/NetworkManager'
NM_IFACE = 'org.freedesktop.NetworkManager'
DBUS_PROPERTIES_IFACE = 'org.freedesktop.DBus.Properties'
NM_DEVICE_IFACE = 'org.freedesktop.NetworkManager.Device'

NM_DEVICE_TYPES = {1: "Ethernet",
                   2: "Wi-Fi",
                   5: "Bluetooth",
                   6: "OLPC",
                   7: "WiMAX",
                   8: "Modem",
                   9: "InfiniBand",
                   10: "Bond",
                   11: "VLAN",
                   12: "ADSL"}

NM_DEVICE_STATES = {0: "Unknown",
                    10: "Unmanaged",
                    20: "Unavailable",
                    30: "Disconnected",
                    40: "Prepare",
                    50: "Config",
                    60: "Need Auth",
                    70: "IP Config",
                    80: "IP Check",
                    90: "Secondaries",
                    100: "Activated",
                    110: "Deactivating",
                    120: "Failed"}


def should_display_lte(diagnostics):
    variant = diagnostics.get('VA')
    variant_data = variant_definitions.get(variant)
    if not variant_data:
        return False
    return variant_data.get('CELLULAR')


def get_ble_devices():
    bus = dbus.SystemBus()
    proxy_object = bus.get_object(BLUEZ_SERVICE_NAME, "/")
    dbus_obj_mgr = dbus.Interface(proxy_object, DBUS_OM_IFACE)
    dbus_objs = dbus_obj_mgr.GetManagedObjects()

    ble_devices = []
    for path, interfaces in dbus_objs.items():
        adapter = interfaces.get(ADAPTER_IFACE)
        if adapter:
            ble_devices.append({
                "Address": str(adapter.get("Address")),
                "Name": str(adapter.get("Name")),
                "Powered": str(adapter.get("Powered")),
                "Discoverable": str(adapter.get("Discoverable")),
                "Pairable": str(adapter.get("Pairable")),
                "Discovering": str(adapter.get("Discovering")),
            })

    log.info('BLE Devices: %s' % ble_devices)

    return ble_devices


def get_lte_devices():
    bus = dbus.SystemBus()
    proxy = bus.get_object(NM_SERVICE_NAME, NM_OBJECT_PATH)
    manager = dbus.Interface(proxy, NM_IFACE)

    # Get all devices known to NM
    devices = manager.GetDevices()

    wifi_devices = []
    for device in devices:
        device_proxy = bus.get_object(NM_SERVICE_NAME, device)
        props_iface = dbus.Interface(device_proxy, DBUS_PROPERTIES_IFACE)
        props = props_iface.GetAll(NM_DEVICE_IFACE)

        device_type = NM_DEVICE_TYPES.get(props.get("DeviceType"), "Unknown")
        device_state = NM_DEVICE_STATES.get(props.get("State"), "Unknown")
        if device_type == "Wi-Fi":
            wifi_devices.append({
                "Interface": str(props.get("Interface")),
                "Type": device_type,
                "Driver": str(props.get("Driver")),
                "State": device_state,
            })

    log.info('WiFi Devices: %s' % wifi_devices)

    return wifi_devices


def set_diagnostics_bt_lte(diagnostics):
    diagnostics['BT'] = any(get_ble_devices())
    diagnostics['LTE'] = any(get_lte_devices())

    return diagnostics


def detect_ecc(diagnostics):
    # The order of the values in the lists is important!
    # It determines which value will be available for which key
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
        serial_number = open("/proc/device-tree/serial-number").readline()
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


if __name__ == '__main__':
    print('set_diagnostics_bt_lte: %s' % set_diagnostics_bt_lte({}))
