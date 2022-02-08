from hw_diag.utilities.dbus_proxy.dbus_ids import DBusIds
from hw_diag.utilities.dbus_proxy.dbus_object import DBusObject


class Sim(DBusObject):
    '''
    Encapsulates modem manager's sim dbus object and provides a few more
    convenience methods.
    '''
    # also known as carrier codes, Mobile network codes etc. shouldn't change very often
    # combination of MCC and MNC. US MCC is between 310 to 316 according to wikipedia
    # taken from following locations:
    # https://en.wikipedia.org/wiki/Mobile_network_codes_in_ITU_region_3xx_(North_America)
    # and https://www.imei.info/carriers/united-states/att/
    ATT_US_OPERATOR_CODES = ['310016', '310030', '310070', '310080', '310090', '310150',
                             '310170', '310280', '310380', '310410', '310560', '310670',
                             '310680', '310950', '311070', '311090', '311180', '311190',
                             '312090', '312680', '313210', '312670', '310311']
    # ATT international operator codes taken from wikipedia mostly South american carriers
    ATT_INT_OPERATOR_CODES = ['901044', '344930', '334010', '334090', '334050',
                              '901018', '334040', '334070', '334080']

    def __init__(self, sim_obj_path: str) -> None:
        super(Sim, self).__init__(DBusIds.DBUS_MM1_SERVICE,
                                  sim_obj_path,
                                  DBusIds.DBUS_MM1_SIM_IF)

    def is_att_sim(self) -> bool:
        operatorid = self.get_property('OperatorIdentifier')
        all_att_operator_codes = self.ATT_US_OPERATOR_CODES + self.ATT_INT_OPERATOR_CODES
        return operatorid in all_att_operator_codes
