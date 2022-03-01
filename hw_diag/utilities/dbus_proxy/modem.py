from hw_diag.utilities.dbus_proxy.dbus_ids import DBusIds
from hw_diag.utilities.dbus_proxy.dbus_object import DBusObject
from hw_diag.utilities.dbus_proxy.sim import Sim


class Modem(DBusObject):
    '''
    Encapsulates modem manager's modem dbus object and provides a few more
    convenience methods.
    Note:: AT commands assume quectel modem
    '''

    FIRMWARE_VER_AT_CMD = 'AT+QGMR'
    UE_MODE_SETTING_WRITE_AT_CMD = 'AT+QNVFW="/nv/item_files/modem/mmode/ue_usage_setting"'
    UE_MODE_SETTING_READ_AT_CMD = 'AT+QNVFR="/nv/item_files/modem/mmode/ue_usage_setting"'
    UE_MODE_DATA_ONLY_VALUE = '01'
    SERVICE_DOMAIN_AT_CMD = 'AT+QCFG="servicedomain"'
    SERVICE_DOMAIN_PS_WRITE_AT_CMD = 'AT+QCFG="servicedomain",1'
    SERVICE_DOMAIN_PS_VALUE = '1'
    REST_AT_CMD = 'AT+CFUN=1,1'

    def __init__(self, modem_obj_path: str) -> None:
        super(Modem, self).__init__(DBusIds.DBUS_MM1_SERVICE,
                                    modem_obj_path,
                                    DBusIds.DBUS_MM1_MODEM_IF)

    def at_command(self, cmd: str, timeout: int = 2000) -> str:
        response = self._object_if.Command(cmd, timeout)
        return response

    def get_fw_version(self) -> str:
        return self.at_command(self.FIRMWARE_VER_AT_CMD)

    def get_ue_mode(self) -> str:
        response = self.at_command(self.UE_MODE_SETTING_READ_AT_CMD)
        values = response.strip().split(' ')
        if len(values) == 2:
            return values[1]
        return ''

    def set_at_value(self, cmd: str, value: str) -> str:
        return self.at_command(cmd + ',' + value)

    def set_ue_mode(self, value: str = UE_MODE_DATA_ONLY_VALUE) -> str:
        return self.set_at_value(self.UE_MODE_SETTING_WRITE_AT_CMD, value)

    def get_service_domain(self) -> str:
        response = self.at_command(self.SERVICE_DOMAIN_AT_CMD)
        values = response.strip().split(',')
        if len(values) == 2:
            return values[1].strip()
        return ''

    def set_service_domain(self, value: str = SERVICE_DOMAIN_PS_VALUE) -> str:
        if value == self.SERVICE_DOMAIN_PS_VALUE:
            return self.at_command(self.SERVICE_DOMAIN_PS_WRITE_AT_CMD + ',' + value)
        return self.at_command(self.SERVICE_DOMAIN_AT_CMD + ',' + value)

    def reset(self) -> str:
        return self.at_command(self.REST_AT_CMD)

    def get_sim(self) -> Sim:
        sim_obj_path = self.get_property('Sim')
        return Sim(sim_obj_path)
