import dbus

from hw_diag.utilities.dbus_proxy.dbus_ids import DBusIds
from hw_diag.utilities.dbus_proxy.dbus_object import DBusObject
from hw_diag.utilities.dbus_proxy.modem import Modem
from hm_pyhelper.logger import get_logger

logging = get_logger(__name__)


class ModemManager(DBusObject):

    def __init__(self) -> None:
        super(ModemManager, self).__init__(DBusIds.DBUS_MM1_SERVICE,
                                           DBusIds.DBUS_MM1_PATH,
                                           DBusIds.DBUS_MM1_IF)
        self._mm_objmanager_iface = dbus.Interface(self._object_proxy,
                                                   DBusIds.DBUS_OBJECTMANAGER_IF)

    def get_all_modems(self) -> list:
        '''
        @rtype: list of all managed Modem objects
        '''
        modem_paths = self._mm_objmanager_iface.GetManagedObjects()
        modems = [Modem(modem_path) for modem_path in modem_paths]
        return modems

    def _do_properties_match(self, actual_properties: dict, desired_properties: dict) -> bool:
        '''
        return true if all properties in desired_properties are present
        and same in actual_properties
        '''
        for prop_key in desired_properties:
            actual_value = actual_properties.get(prop_key).strip()
            desired_value = desired_properties.get(prop_key)
            logging.debug(f'matching value of {prop_key} - '
                          f'actual : {actual_value} and desired: {desired_value}')
            if actual_value not in desired_value:
                logging.info(f'actual value: {actual_value} does not match '
                             f'any in desired: {desired_value}')
                return False
        # all matched
        return True

    def find_modem_by_properties(self, desired_properties: dict) -> Modem:
        '''
        find modem for which all supplied properties match
        @param properties: dict of properties to match
        @rtype: Modem object or None if properties don't match any modem
        '''
        modems = self.get_all_modems()

        # iterate over all object paths
        for modem in modems:
            props = modem.get_properties()
            if self._do_properties_match(props, desired_properties):
                return modem


if __name__ == '__main__':

    mm = ModemManager()

    # quectel unique properties
    quectel_unique_properties = {'Revision': ['EG25GGBR07A08M2G', 'EG25GGBR07A07M2G']}

    modem_proxy = mm.find_modem_by_properties(quectel_unique_properties)
    if modem_proxy:
        print(modem_proxy.get_fw_version())

    modems = mm.get_all_modems()
    for modem in modems:
        print(f'modem firmware version : {modem.get_fw_version()}')
        mode_value = modem.get_ue_mode()
        mode_desc = 'data only' if mode_value == Modem.UE_MODE_DATA_ONLY_VALUE else 'data and voice'
        print(f'modem UE mode_desc : {mode_desc} mode_value: {mode_value}')
        print(modem.get_service_domain())
        sim = modem.get_sim()
        print(sim.get_property('OperatorName'))
        print(sim.get_property('OperatorIdentifier'))
