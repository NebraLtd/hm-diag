import dbus
import psutil
from typing import Union
from urllib.parse import urlparse
from hm_pyhelper.logger import get_logger
from hm_pyhelper.miner_param import get_public_keys_rust, config_search_param, \
                                    parse_i2c_bus, parse_i2c_address, get_ecc_location
from hm_pyhelper.hardware_definitions import variant_definitions, get_variant_attribute, \
                                             is_rockpi
from retry import retry


logging = get_logger(__name__)

CPUINFO_SERIAL_KEY = "serial"
DBUS_PROPERTIES = 'org.freedesktop.DBus.Properties'
DBUS_OBJECTMANAGER = 'org.freedesktop.DBus.ObjectManager'

# BlueZ
DBUS_BLUEZ_SERVICE_NAME = 'org.bluez'
DBUS_ADAPTER_IFACE = 'org.bluez.Adapter1'

# NetworkManager
DBUS_NM_SERVICE_NAME = 'org.freedesktop.NetworkManager'
DBUS_NM_OBJECT_PATH = '/org/freedesktop/NetworkManager'
DBUS_NM_IFACE = 'org.freedesktop.NetworkManager'
DBUS_NM_DEVICE_IFACE = 'org.freedesktop.NetworkManager.Device'

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

# ModemManager
DBUS_MM1_SERVICE = 'org.freedesktop.ModemManager1'
DBUS_MM1_PATH = '/org/freedesktop/ModemManager1'
DBUS_MM1_IF = 'org.freedesktop.ModemManager1'
DBUS_MM1_IF_MODEM = 'org.freedesktop.ModemManager1.Modem'
DBUS_MM1_IF_MODEM_SIMPLE = 'org.freedesktop.ModemManager1.Modem.Simple'
DBUS_MM1_IF_MODEM_3GPP = 'org.freedesktop.ModemManager1.Modem.Modem3gpp'
DBUS_MM1_IF_MODEM_CDMA = 'org.freedesktop.ModemManager1.Modem.ModemCdma'

MM_MODEM_CAPABILITY = {
    'NONE': 0,
    'POTS': 1 << 0,
    'CDMA_EVDO': 1 << 1,
    'GSM_UMTS': 1 << 2,
    'LTE': 1 << 3,
    'ADVANCED': 1 << 4,
    'IRIDIUM': 1 << 5,
    'ANY': 0xFFFFFFFF}


def should_display_lte(diagnostics):
    variant = diagnostics.get('VA')
    variant_data = variant_definitions.get(variant)
    if not variant_data:
        return False
    return variant_data.get('CELLULAR')


def get_ble_devices():
    logging.info("Retrieving list of BLE device(s)")

    ble_devices = []
    try:
        bus = dbus.SystemBus()
        proxy_object = bus.get_object(DBUS_BLUEZ_SERVICE_NAME, "/")
        dbus_obj_mgr = dbus.Interface(proxy_object, DBUS_OBJECTMANAGER)
        dbus_objs = dbus_obj_mgr.GetManagedObjects()
        for path, interfaces in dbus_objs.items():
            adapter = interfaces.get(DBUS_ADAPTER_IFACE)
            if adapter:
                ble_devices.append({
                    "Address": str(adapter.get("Address")),
                    "Name": str(adapter.get("Name")),
                    "Powered": str(adapter.get("Powered")),
                    "Discoverable": str(adapter.get("Discoverable")),
                    "Pairable": str(adapter.get("Pairable")),
                    "Discovering": str(adapter.get("Discovering")),
                })

        logging.info(f"Found the following BLE Devices: {ble_devices}")
    except dbus.exceptions.DBusException as e:
        logging.error(e.get_dbus_message())
    except Exception as e:
        logging.error(f"Error while retrieving list of BLE devices: {e}")

    return ble_devices


def get_wifi_devices():
    logging.info("Retrieving list of WiFi device(s)")

    wifi_devices = []
    try:
        bus = dbus.SystemBus()
        proxy = bus.get_object(DBUS_NM_SERVICE_NAME, DBUS_NM_OBJECT_PATH)
        manager = dbus.Interface(proxy, DBUS_NM_IFACE)
        devices = manager.GetDevices()

        for device in devices:
            device_proxy = bus.get_object(DBUS_NM_SERVICE_NAME, device)
            props_iface = dbus.Interface(device_proxy, DBUS_PROPERTIES)
            props = props_iface.GetAll(DBUS_NM_DEVICE_IFACE)

            device_type = NM_DEVICE_TYPES.get(props.get("DeviceType"),
                                              "Unknown")
            device_state = NM_DEVICE_STATES.get(props.get("State"), "Unknown")

            if device_type == "Wi-Fi":
                wifi_devices.append({
                    "Interface": str(props.get("Interface")),
                    "Type": device_type,
                    "Driver": str(props.get("Driver")),
                    "State": device_state,
                })

        logging.info(f"Found the following WiFi Devices: {wifi_devices}")
    except dbus.exceptions.DBusException as e:
        logging.error(e.get_dbus_message())
    except Exception as e:
        logging.error(f"Error while retrieving list of WiFi devices: {e}")

    return wifi_devices


def get_lte_devices():
    logging.info("Retrieving list of LTE device(s)")

    lte_devices = []
    try:
        bus = dbus.SystemBus()
        proxy = bus.get_object(DBUS_MM1_SERVICE, DBUS_MM1_PATH)
        manager = dbus.Interface(proxy, DBUS_OBJECTMANAGER)
        modems = manager.GetManagedObjects()

        for modem in modems:
            modem_proxy = bus.get_object(DBUS_MM1_SERVICE, modem)
            props_iface = dbus.Interface(modem_proxy, DBUS_PROPERTIES)
            props = props_iface.GetAll(DBUS_MM1_IF_MODEM)

            model = props.get("Model")
            manufacturer = props.get("Manufacturer")
            capabilities = props.get("CurrentCapabilities")
            equipment_id = props.get("EquipmentIdentifier")

            if capabilities & MM_MODEM_CAPABILITY['LTE'] or \
                    capabilities & MM_MODEM_CAPABILITY['LTE_ADVANCED']:
                lte_devices.append({
                    "Model": str(model),
                    "Manufacturer": str(manufacturer),
                    "EquipmentIdentifier": str(equipment_id),
                })

        logging.info(f"Found the following LTE Devices: {lte_devices}")
    except dbus.exceptions.DBusException as e:
        logging.error(e.get_dbus_message())
    except Exception as e:
        logging.error(f"Error while retrieving list of LTE devices: {e}")

    return lte_devices


def set_diagnostics_bt_lte(diagnostics):
    diagnostics['BT'] = any(get_ble_devices())
    diagnostics['LTE'] = any(get_lte_devices())

    return diagnostics


def detect_ecc(diagnostics):
    # The order of the values in the lists is important!
    # It determines which value will be available for which key
    i2c_bus = ''
    try:
        # Example SWARM_KEY_URI: "ecc://i2c-1:96?slot=0"
        swarm_key_uri = get_ecc_location()
        parse_result = urlparse(swarm_key_uri)
        i2c_bus = parse_i2c_bus(parse_result.hostname)
        i2c_address = parse_i2c_address(parse_result.port)

    except Exception as e:
        logging.warn("Unable to lookup SWARM_KEY_URI from hardware definitions, "
                     "Exception message: {}".format(e))

    if not i2c_bus or not i2c_bus.isnumeric():
        logging.warn("Unable to lookup storage bus from hardware definitions, "
                     "falling back to the default.")
        i2c_bus = '1'
        i2c_address = '60'

    commands = [
        f'i2cdetect -y {i2c_bus}'
    ]

    parameters = [f'{i2c_address} --']
    keys = ["ECC"]

    for (command, param, key) in zip(commands, parameters, keys):
        try:
            diagnostics[key] = config_search_param(command, param)
        except Exception as e:
            logging.error(e)


def fetch_serial_number() -> Union[str, None]:
    diag = {}
    get_serial_number(diag)
    return diag.get("serial_number")


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
        cpuinfo = load_cpu_info()
        serial_number = ""
        if has_valid_serial(cpuinfo):
            serial_number = cpuinfo[CPUINFO_SERIAL_KEY]
        else:
            serial_number = open("/proc/device-tree/serial-number").readline() \
                .rstrip('\x00')
    except FileNotFoundError as e:
        raise e
    except PermissionError as e:
        raise e

    diagnostics["serial_number"] = serial_number


def has_valid_serial(cpuinfo: dict) -> bool:
    if CPUINFO_SERIAL_KEY not in cpuinfo:
        return False

    # Check if serial number is all 0s...
    serial_number = cpuinfo[CPUINFO_SERIAL_KEY]
    if all(c in '0' for c in str(serial_number)):
        return False

    return True


def load_cpu_info() -> dict:
    '''
    returns /proc/cpuinfo as dict, keys are case-insensitive
    '''
    cpuinfo = {}
    try:
        with open("/proc/cpuinfo", "r") as f:
            lines = f.readlines()
            for line in lines:
                pair = line.split(":")
                if len(pair) == 2:
                    cpuinfo[pair[0].strip().lower()] = pair[1].strip()
    except Exception as e:
        logging.warning(f"failed to load /proc/cpuinfo: {e}")
    return cpuinfo


@retry(Exception, tries=5, delay=5, max_delay=15, backoff=2, logger=logging)
def lora_module_test():
    """
    Checks the status of the lore module.
    Returns true or false.
    """
    result = None
    pkt_fwd_diag_file = "/var/pktfwd/diagnostics"
    while result is None:
        try:
            # The Pktfwder container creates this file
            # to pass over the status.
            with open(pkt_fwd_diag_file) as data:
                lora_status = data.read()
                if lora_status == "true":
                    result = True
                else:
                    result = False
        except FileNotFoundError as e:
            # Packet forwarder container hasn't started
            logging.error(f"File {pkt_fwd_diag_file} doesn't exit yet. "
                          f"Most likely pktfwd container hasn't started yet")
            raise e

    return result


def get_public_keys_and_ignore_errors():
    error_msg = None
    try:
        public_keys = get_public_keys_rust()
        if not public_keys:
            public_keys = {
                'name': error_msg,
                'key': error_msg
            }
    except Exception as e:
        logging.error(e)
        public_keys = {
            'name': error_msg,
            'key': error_msg
        }

    return public_keys


def is_button_present(diagnostics):
    variant = diagnostics.get('VA')
    button = get_variant_attribute(variant, 'BUTTON')
    return bool(button)


def get_device_metrics():
    if is_rockpi():
        try:
            temperature = psutil.sensors_temperatures()['soc-thermal'][0].current
        except Exception:
            temperature = 0
    else:
        try:
            temperature = psutil.sensors_temperatures()['cpu_thermal'][0].current
        except Exception:
            temperature = 0

    memory_used = psutil.virtual_memory().total - psutil.virtual_memory().available

    return {
        'cpu': psutil.cpu_percent(),
        'memory_total': psutil.virtual_memory().total,
        'memory_used': memory_used,
        'disk_total': psutil.disk_usage('/').total,
        'disk_used': psutil.disk_usage('/').used,
        'temperature': temperature
    }


if __name__ == '__main__':
    logging.info('get_wifi_devices(): %s' % get_wifi_devices())
    logging.info('set_diagnostics_bt_lte(): %s' % set_diagnostics_bt_lte({}))
