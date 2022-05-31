import dbus
from hw_diag.utilities.dbus_proxy.dbus_ids import DBusIds
from hw_diag.utilities.dbus_proxy.dbus_object import DBusObject
from hm_pyhelper.logger import get_logger

logging = get_logger(__name__)


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


if __name__ == '__main__':
    nm = NetworkManager()
    print('Network connectivity: ', nm.get_connect_state())
    print('Is connected: ', nm.is_connected())
