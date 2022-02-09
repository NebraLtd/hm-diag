# 
# Few dbus proxy classes that encapsulate dbus calls in an easy to use/read way.
#

import dbus

class DBusIds:
    '''DBus Identities'''
    
    DBUS_PROPERTIES_IF = 'org.freedesktop.DBus.Properties'
    DBUS_OBJECTMANAGER_IF = 'org.freedesktop.DBus.ObjectManager'
    
    DBUS_MM1_SERVICE = 'org.freedesktop.ModemManager1'
    DBUS_MM1_PATH = '/org/freedesktop/ModemManager1'
    DBUS_MM1_IF = 'org.freedesktop.ModemManager1'
    DBUS_MM1_MODEM_IF = 'org.freedesktop.ModemManager1.Modem'
    
    SYSTEMD_SERVICE = 'org.freedesktop.systemd1'
    SYSTEMD_PATH = '/org/freedesktop/systemd1'
    SYSTEMD_MANAGER_IF = 'org.freedesktop.systemd1.Manager'
    SYSTEMD_UNIT_IF  = 'org.freedesktop.systemd1.Unit'

class DBusObject(object):
    '''Base class for various dbus objects'''
    
    def __init__(self, service, path, interface):
        self._system_bus = dbus.SystemBus()
        self._object_proxy = self._system_bus.get_object(service, path)
        self._object_if = dbus.Interface(self._object_proxy, interface)
        self._properties_iface = dbus.Interface(self._object_proxy, DBusIds.DBUS_PROPERTIES_IF)
        
    def get_properties(self):
        props = self._properties_iface.GetAll(self._object_if.dbus_interface)
        return props
    
    def get_property(self, property_name):
        prop = self._properties_iface.Get(self._object_if.dbus_interface, property_name)
        return prop
        
class Modem(DBusObject):
    '''
    Encapsulates modem manager's modem dbus object and provides a few more
    convenience methods.
    Note:: AT commands assume quectel modem
    '''
    
    FIRMWARE_VER_AT_CMD  = 'AT+QGMR'
    UE_MODE_SETTING_WRITE_AT_CMD = 'AT+QNVFW="/nv/item_files/modem/mmode/ue_usage_setting"'
    UE_MODE_SETTING_READ_AT_CMD = 'AT+QNVFR="/nv/item_files/modem/mmode/ue_usage_setting"'
    UE_MODE_DATA_ONLY_VALUE = '01'
    SERVICE_DOMAIN_AT_CMD = 'AT+QCFG=“servicedomain”'
    SERVICE_DOMAIN_PS_VALUE = '1,1'
    
    def __init__(self, modem_obj_path):
        super(Modem, self).__init__(DBusIds.DBUS_MM1_SERVICE, modem_obj_path, DBusIds.DBUS_MM1_MODEM_IF)

    def at_command(self, cmd, timeout=2000):
        response = self._object_if.Command(cmd, timeout)
        return response
    
    def get_fw_version(self):
        return self.at_command(self.FIRMWARE_VER_AT_CMD)
    
    def get_UE_mode(self):
        response = self.at_command(self.UE_MODE_SETTING_READ_AT_CMD)
        values = response.strip().split(' ')
        if len(values) == 2:
            return values[1]
    
    def set_UE_Mode(self, value = UE_MODE_DATA_ONLY_VALUE):
        return self.at_command(self.UE_MODE_SETTING_WRITE_AT_CMD + ',' + value)
    
    def get_service_domain(self, value = SERVICE_DOMAIN_PS_VALUE):
        return self.at_command(self.SERVICE_DOMAIN_AT_CMD)
    
    def set_service_domain(self, value = SERVICE_DOMAIN_PS_VALUE):
        return self.at_command(self.SERVICE_DOMAIN_AT_CMD + ',' + value)
    
    def ensure_data_centric_mode(self):
        if self.get_UE_mode() != self.UE_MODE_DATA_ONLY_VALUE:
            self.set_UE_Mode(self.UE_MODE_DATA_ONLY_VALUE)
        # EG25-G doesn't seem to support this command
        # if self.get_service_domain() != self.SERVICE_DOMAIN_PS_VALUE:
        #     self.set_service_domain(self.SERVICE_DOMAIN_PS_VALUE)

class ModemManager(DBusObject):

    def __init__(self, *args, **kwargs):
        super(ModemManager, self).__init__(DBusIds.DBUS_MM1_SERVICE, DBusIds.DBUS_MM1_PATH, DBusIds.DBUS_MM1_IF)
        self._mm_objmanager_iface = dbus.Interface(self._object_proxy, DBusIds.DBUS_OBJECTMANAGER_IF)
        
    def all_modems(self):
        '''
        @rtype: list of all managed Modem objects
        '''
        modem_paths = self._mm_objmanager_iface.GetManagedObjects()
        modems = [Modem(modem_path) for modem_path in modem_paths]
        return modems
    
    def find_modem_by_properties(self, properties):
        '''
        find modem for which all supplied properties match
        @param properties: dict of properties to match
        @rtype: Modem object or None if properties don't match any modem
        '''      
        modems = self.all_modems()
        
        # iterate over all object paths
        for modem in modems:
            props = modem.get_properties()
            
            for prop in properties:
                if props.get(prop) != properties[prop]:
                    return None
            return modem

    
class Unit(DBusObject):
    '''
    represents a systemd unit with a few convenience methods
    '''
    def __init__(self, unit_obj_path):
        super(Unit, self).__init__(DBusIds.SYSTEMD_SERVICE, unit_obj_path, DBusIds.SYSTEMD_UNIT_IF)
    
    def start(self, mode='fail'):
        job_path = self._object_if.Start(mode)
        return job_path

    def stop(self, mode='fail'):
        job_path = self._object_if.Stop(mode)
        return job_path
    
    def _wait_state(self, target_state, timeout):
        sleep_time = 0.1 # seconds
        max_polls = timeout / sleep_time
        for i in max_polls:
            if self.get_property('SubState').trim() == target_state:
                return True
            time.sleep(sleep_time)
        return False
    
    def wait_stop(self, mode='fail', timeout=2):
        '''
        issues stop command and wait for max timeout secs for it to stop
        @param mode: dbus unit start/stop modes. Default is good for most cases
        @param timeout: max time to wait for stop in secs
        @rtype: true if stopped else false
        '''
        self.stop()
        return self._wait_state('dead', timeout)
    
    def wait_start(self, mode='fail', timeout=2):
        '''
        issues start command and wait for max timeout secs for it to stop
        @param mode: dbus unit start/stop modes. Default is good for most cases
        @param timeout: max time to wait for stop in secs
        @rtype: true if started else false
        '''
        self.start(mode)
        return self._wait_state('running', timeout)
    
    def isRunning(self):
        return self.get_property('SubState').trim() == 'running'
    
    def isStopped(self):
        return self.get_property('SubState').trim() == 'dead'
        
    
    
class Systemd(DBusObject):
    def __init__(self):
        super(Systemd, self).__init__(DBusIds.SYSTEMD_SERVICE, DBusIds.SYSTEMD_PATH, DBusIds.SYSTEMD_MANAGER_IF)
    
    def get_unit(self, servicename):
        unit_path = self._object_if.GetUnit(servicename)
        unit_proxy = Unit(unit_path)
        return unit_proxy
        
        
if __name__ == '__main__':
    import time
    mm = ModemManager()
    systemd = Systemd()
    
    # quectel unique properties
    quectel_unique_properties = { 'Manufacturer' : 'QUALCOMM INCORPORATED', 
                         'Model' : 'QUECTEL Mobile Broadband Module', 
                         'Revision' : 'EG25GGBR07A08M2G' 
                         }
    modem_proxy = mm.find_modem_by_properties(quectel_unique_properties)
    if modem_proxy:
        print(modem_proxy.get_fw_version())
    
    modems = mm.all_modems()
    for modem in modems:
        print(modem.get_fw_version())
        print(modem.get_UE_mode())
        # print(modem.get_service_domain())
        
    unit_proxy = systemd.get_unit('ModemManager.service')

    if unit_proxy.get_property('SubState') == 'running':
        print('mm is running')
    
    unit_proxy.stop('fail')
    while unit_proxy.get_property('SubState') != 'dead':
        time.sleep(1)
    print('mm is dead')
    
    unit_proxy.start('fail')
    while unit_proxy.get_property('SubState') != 'running':
        time.sleep(1)
    print('mm is running')
