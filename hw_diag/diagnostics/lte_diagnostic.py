import dbus

from hm_pyhelper.diagnostics.diagnostic import Diagnostic
from hm_pyhelper.logger import get_logger

# Diagnostics keys
KEY = 'LTE'
FRIENDLY_NAME = "lte"

DBUS_PROPERTIES = 'org.freedesktop.DBus.Properties'
DBUS_OBJECTMANAGER = 'org.freedesktop.DBus.ObjectManager'

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

NO_LTE_DEVICES_MSG = "ModemManager is working but, no LTE devices detected."

LOGGER = get_logger(__name__)


class LteDiagnostic(Diagnostic):
    def __init__(self):
        super(LteDiagnostic, self).__init__(KEY, FRIENDLY_NAME)

    def perform_test(self, diagnostics_report):
        LOGGER.info("Retrieving list of LTE device(s)")

        try:
            lte_devices = get_lte_devices()
            LOGGER.info(f"Found the following LTE devices: {lte_devices}")
            self.process_lte_devices(lte_devices, diagnostics_report)

        except dbus.exceptions.DBusException as e:
            LOGGER.error(e.get_dbus_message())
            diagnostics_report.record_failure(e, self)

        except Exception as e:
            LOGGER.error(f"Error while retrieving list of LTE devices: {e}")
            diagnostics_report.record_failure(e, self)

    def process_lte_devices(self, lte_devices, diagnostics_report):
        if len(lte_devices) > 0:
            diagnostics_report.record_result(lte_devices, self)
        else:
            diagnostics_report.record_failure(NO_LTE_DEVICES_MSG, self)


def get_lte_devices():
    lte_devices = []
    system_bus = dbus.SystemBus()
    proxy = system_bus.get_object(DBUS_MM1_SERVICE, DBUS_MM1_PATH)
    manager = dbus.Interface(proxy, DBUS_OBJECTMANAGER)
    modems = manager.GetManagedObjects()

    for modem in modems:
        append_lte_device_from_modem(lte_devices, modem, system_bus)

    LOGGER.info(f"Found the following LTE Devices: {lte_devices}")
    return lte_devices


def append_lte_device_from_modem(lte_devices, modem, system_bus):
    modem_proxy = system_bus.get_object(DBUS_MM1_SERVICE, modem)
    props_iface = dbus.Interface(modem_proxy, DBUS_PROPERTIES)
    props = props_iface.GetAll(DBUS_MM1_IF_MODEM)

    model = props.get("Model")
    manufacturer = props.get("Manufacturer")
    capabilities = props.get("CurrentCapabilities")
    equipment_id = props.get("EquipmentIdentifier")

    is_lte = capabilities & MM_MODEM_CAPABILITY['LTE'] or \
        capabilities & MM_MODEM_CAPABILITY['LTE_ADVANCED']

    if is_lte:
        lte_devices.append({
            "Model": str(model),
            "Manufacturer": str(manufacturer),
            "EquipmentIdentifier": str(equipment_id)
        })

    return lte_devices
