
from hw_diag.utilities.dbus_proxy.dbus_ids import DBusIds
from hw_diag.utilities.dbus_proxy.dbus_object import DBusObject
from hw_diag.utilities.dbus_proxy.systemd_unit import SystemDUnit


class Systemd(DBusObject):
    def __init__(self) -> None:
        super(Systemd, self).__init__(DBusIds.SYSTEMD_SERVICE,
                                      DBusIds.SYSTEMD_PATH,
                                      DBusIds.SYSTEMD_MANAGER_IF)

    def get_unit(self, servicename: str) -> SystemDUnit:
        unit_path = self._object_if.GetUnit(servicename)
        unit_proxy = SystemDUnit(unit_path)
        return unit_proxy


if __name__ == '__main__':
    systemd = Systemd()
    unit_proxy = systemd.get_unit(DBusIds.MODEM_MANAGER_UNIT_NAME)

    if unit_proxy.get_property('SubState') == 'running':
        print('mm is running')

    unit_proxy.wait_stop()
    print('mm is dead')

    unit_proxy.wait_start()
    print('mm is running')
