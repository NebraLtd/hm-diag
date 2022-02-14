import dbus
from hm_pyhelper.diagnostics import DiagnosticsReport

from hm_pyhelper.diagnostics.diagnostic import Diagnostic
from hm_pyhelper.logger import get_logger

LOGGER = get_logger(__name__)


class BtDiagnostic(Diagnostic):
    # Diagnostics keys
    KEY = 'BT'
    FRIENDLY_NAME = "bluetooth"

    # D-Bus constants
    DBUS_PROPERTIES = 'org.freedesktop.DBus.Properties'
    DBUS_OBJECTMANAGER = 'org.freedesktop.DBus.ObjectManager'
    DBUS_BLUEZ_SERVICE_NAME = 'org.bluez'
    DBUS_ADAPTER_IFACE = 'org.bluez.Adapter1'

    # Error messages
    NO_BT_DEVICES_MSG = "Bluez is working but, no Bluetooth devices detected."

    def __init__(self):
        super(BtDiagnostic, self).__init__(self.KEY, self.FRIENDLY_NAME)

    def perform_test(self, diagnostics_report: DiagnosticsReport) -> None:
        LOGGER.debug("Retrieving list of Bluetooth device(s)")

        try:
            bt_devices = self.get_bt_devices()
            LOGGER.info(f"Found the following Bluetooth devices: {bt_devices}")
            self.process_bt_devices(bt_devices, diagnostics_report)

        except dbus.exceptions.DBusException as e:
            LOGGER.error(e.get_dbus_message())
            diagnostics_report.record_failure(e, self)

        except Exception as e:
            LOGGER.error("Error while retrieving list of Bluetooth devices: %s"
                         % e)
            diagnostics_report.record_failure(e, self)

    def process_bt_devices(self, bt_devices: list, diagnostics_report: DiagnosticsReport) -> None:
        if len(bt_devices) > 0:
            diagnostics_report.record_result(bt_devices, self)
        else:
            diagnostics_report.record_failure(self.NO_BT_DEVICES_MSG, self)

    def get_bt_devices(self) -> list:
        bt_devices = []
        bus = dbus.SystemBus()
        proxy_object = bus.get_object(self.DBUS_BLUEZ_SERVICE_NAME, "/")
        dbus_obj_mgr = dbus.Interface(proxy_object, self.DBUS_OBJECTMANAGER)
        dbus_objs = dbus_obj_mgr.GetManagedObjects()
        for path, interfaces in dbus_objs.items():
            self.append_bt_devices_from_interfaces(bt_devices, interfaces)

        return bt_devices

    def append_bt_devices_from_interfaces(self, bt_devices: list, dbus_interfaces: list) -> list:
        adapter = dbus_interfaces.get(self.DBUS_ADAPTER_IFACE)

        if adapter:
            bt_devices.append({
                "Address": str(adapter.get("Address")),
                "Name": str(adapter.get("Name")),
                "Powered": str(adapter.get("Powered")),
                "Discoverable": str(adapter.get("Discoverable")),
                "Pairable": str(adapter.get("Pairable")),
                "Discovering": str(adapter.get("Discovering")),
            })

        return bt_devices
