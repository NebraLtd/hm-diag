
class DBusIds:
    """DBus Identities"""
    # Object manager
    DBUS_PROPERTIES_IF = 'org.freedesktop.DBus.Properties'
    DBUS_OBJECTMANAGER_IF = 'org.freedesktop.DBus.ObjectManager'

    # Modem manager
    DBUS_MM1_SERVICE = 'org.freedesktop.ModemManager1'
    DBUS_MM1_PATH = '/org/freedesktop/ModemManager1'
    DBUS_MM1_IF = 'org.freedesktop.ModemManager1'
    DBUS_MM1_MODEM_IF = 'org.freedesktop.ModemManager1.Modem'
    DBUS_MM1_SIM_IF = 'org.freedesktop.ModemManager1.Sim'
    DBUS_MM1_MODEM_SIMPLE_IF = 'org.freedesktop.ModemManager1.Modem.Simple'
    DBUS_MM1_MODEM_3GPP_IF = 'org.freedesktop.ModemManager1.Modem.Modem3gpp'
    DBUS_MM1_MODEM_CDMA_IF = 'org.freedesktop.ModemManager1.Modem.ModemCdma'

    # Network manager
    DBUS_NM_SERVICE = 'org.freedesktop.NetworkManager'
    DBUS_NM_PATH = '/org/freedesktop/NetworkManager'
    DBUS_NM_IF = 'org.freedesktop.NetworkManager'

    # Systemd
    SYSTEMD_SERVICE = 'org.freedesktop.systemd1'
    SYSTEMD_PATH = '/org/freedesktop/systemd1'
    SYSTEMD_MANAGER_IF = 'org.freedesktop.systemd1.Manager'
    SYSTEMD_UNIT_IF = 'org.freedesktop.systemd1.Unit'

    # Systemd units
    MODEM_MANAGER_UNIT_NAME = 'ModemManager.service'
    NETWORK_MANAGER_UNIT_NAME = 'NetworkManager.service'
