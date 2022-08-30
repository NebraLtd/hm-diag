import dbus
from hw_diag.utilities.dbus_proxy.dbus_ids import DBusIds
from hw_diag.utilities.dbus_proxy.dbus_object import DBusObject
from hm_pyhelper.logger import get_logger

LOGGER = get_logger(__name__)


class NetworkManager(DBusObject):
    nm_state = {
        0: "Unknown",
        10: "Asleep",
        20: "Disconnected",
        30: "Disconnecting",
        40: "Connecting",
        50: "Connected-Local",
        60: "Connected-Site",
        70: "Connected-Global",
    }

    def __init__(self) -> None:
        super(NetworkManager, self).__init__(DBusIds.DBUS_NM_SERVICE,
                                             DBusIds.DBUS_NM_PATH,
                                             DBusIds.DBUS_NM_IF)
        self._network_manager_iface = dbus.Interface(self._object_proxy,
                                                     DBusIds.DBUS_NM_IF)

    def get_connect_state(self) -> str:
        """Get NetworkManager Connectivity State"""
        state = self._network_manager_iface.state()
        state_string = self.nm_state.get(state, 'Unknown')
        return state_string

    def is_connected(self) -> bool:
        return 'Connected' in self.get_connect_state()

    def get_gateways(self) -> list:
        active_connections = self.get_property('ActiveConnections')

        gateways = []
        for connection_path in active_connections:
            connection_proxy = self._system_bus.get_object(DBusIds.DBUS_NM_SERVICE, connection_path)
            connection_props_if = dbus.Interface(connection_proxy,
                                                 dbus_interface=DBusIds.DBUS_PROPERTIES_IF)
            connection_props = connection_props_if.GetAll(DBusIds.DBUS_NM_ACTIVE_CONNECTION_IF)
            connection_ipv4_path = connection_props.get("Ip4Config")

            ipv4_obj = self._system_bus.get_object(DBusIds.DBUS_NM_SERVICE, connection_ipv4_path)
            ipv4_props_if = dbus.Interface(ipv4_obj, dbus_interface=DBusIds.DBUS_PROPERTIES_IF)
            ipv4_props = ipv4_props_if.GetAll(DBusIds.DBUS_NM_IPV4CONFIG_IF)
            gateway = str(ipv4_props.get("Gateway"))

            if gateway:
                gateways.append(gateway)

        # Remove duplicated gateways
        gateways = list(set(gateways))

        return gateways


if __name__ == '__main__':
    nm = NetworkManager()
    print('Network connectivity: ', nm.get_connect_state())
    print('Is connected: ', nm.is_connected())
