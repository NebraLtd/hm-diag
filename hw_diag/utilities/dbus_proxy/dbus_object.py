import dbus

from hw_diag.utilities.dbus_proxy.dbus_ids import DBusIds


class DBusObject(object):
    '''Base class for various dbus objects'''

    def __init__(self, service: str, path: str, interface: str) -> None:
        self._system_bus = dbus.SystemBus()
        self._object_proxy = self._system_bus.get_object(service, path)
        self._object_if = dbus.Interface(self._object_proxy, interface)
        self._properties_iface = dbus.Interface(self._object_proxy, DBusIds.DBUS_PROPERTIES_IF)

    def get_properties(self):
        props = self._properties_iface.GetAll(self._object_if.dbus_interface)
        return props

    def get_property(self, property_name: str) -> str:
        prop = self._properties_iface.Get(self._object_if.dbus_interface, property_name)
        return prop
