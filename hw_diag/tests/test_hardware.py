import unittest
from unittest.mock import patch, MagicMock

import pytest
from dbus import DBusException

from hw_diag.utilities.hardware import (
    DTPARAM_CONFIG_VAR_NAMES,
    DTPARAM_CONFIG_VAR_NAME,
    EXT_ANT_DTPARAM,
    get_lte_devices, detect_ecc,
    get_public_keys_and_ignore_errors,
    get_wifi_devices, get_ble_devices,
    has_external_antenna_support,
    is_external_antenna_enabled,
    set_external_antenna_enabled,
)


class TestHardware(unittest.TestCase):
    ECC_I2C_DETECT_PATTERN = '60 --'

    @patch('hw_diag.utilities.hardware.get_public_keys_rust')
    def test_get_public_keys_no_error(self, mocked_get_public_keys_rust):
        mocked_get_public_keys_rust.return_value = {
            'key': 'foo',
            'name': 'bar'
        }
        keys = get_public_keys_and_ignore_errors()

        self.assertEqual(keys['key'], 'foo')
        self.assertEqual(keys['name'], 'bar')

    @patch('hw_diag.utilities.hardware.get_public_keys_rust')
    def test_get_public_keys_with_error(self, mocked_get_public_keys_rust):
        mocked_get_public_keys_rust.return_value = False
        keys = get_public_keys_and_ignore_errors()

        self.assertIsNone(keys['key'])
        self.assertIsNone(keys['name'])

    @patch('dbus.SystemBus')
    @patch('dbus.Interface')
    def test_get_ble_devices_success(self, mocked_interface, mocked_bus):
        # Prepare mocked BLE devices
        mocked_ble_devices = {
            '/org/bluez/hci0': {
                'org.bluez.Adapter1': {
                    'Address': '00:E0:4C:19:D2:91',
                    'AddressType': 'public',
                    'Name': 'ble0',
                    'Alias': 'ble0',
                    'Class': '1835268',
                    'Powered': '1',
                    'Discoverable': '1',
                    'DiscoverableTimeout': 0,
                    'Pairable': '1',
                    'PairableTimeout': 0,
                    'Discovering': '0',
                    'UUIDs': [],
                    'Modalias': 'usb:v1D6Bp0246d0535'
                }
            }
        }

        # Set mocked BLE devices in dbus
        mocked_interface = mocked_interface.return_value
        mocked_interface.GetManagedObjects.return_value = mocked_ble_devices

        # Mock the names of services returned by the bus
        mocked_bus = mocked_bus.return_value
        mocked_bus.list_names.return_value = ['org.bluez']

        # Retrieve list of BLE devices
        ble_devices = get_ble_devices()

        # Assertion
        self.assertIsInstance(ble_devices, list)
        self.assertEqual(len(ble_devices), 1)
        self.assertDictEqual(ble_devices[0], {
            'Address': '00:E0:4C:19:D2:91',
            'Name': 'ble0',
            'Powered': '1',
            'Discoverable': '1',
            'Pairable': '1',
            'Discovering': '0',
        })

    @patch('dbus.SystemBus')
    @patch('dbus.Interface')
    def test_get_ble_devices_no_devices(self, mocked_interface, _):
        # Prepare mocked BLE devices
        mocked_ble_devices = {}

        # Set mocked BLE devices in dbus
        mocked_interface = mocked_interface.return_value
        mocked_interface.GetManagedObjects.return_value = mocked_ble_devices

        # Retrieve list of BLE devices
        ble_devices = get_ble_devices()

        # Assertion
        self.assertIsInstance(ble_devices, list)
        self.assertEqual(len(ble_devices), 0)

    @patch('dbus.SystemBus')
    @patch('dbus.Interface')
    def test_get_ble_devices_no_service(self, _, mocked_bus):
        # Mock the names of services returned by the bus
        mocked_bus = mocked_bus.return_value
        mocked_bus.list_names.return_value = ['something.Else']

        # Retrieve list of BLE devices
        ble_devices = get_ble_devices()

        # Assertion
        self.assertIsInstance(ble_devices, list)
        self.assertEqual(len(ble_devices), 0)

    @patch('dbus.SystemBus')
    @patch('dbus.Interface', side_effect=DBusException('Not authorized'))
    def test_get_ble_devices_exception(self, mocked_interface, _):
        # Prepare mocked BLE devices
        mocked_ble_devices = {}

        # Set mocked BLE devices in dbus
        mocked_interface = mocked_interface.return_value
        mocked_interface.GetManagedObjects.return_value = mocked_ble_devices

        # Retrieve list of BLE devices
        ble_devices = get_ble_devices()

        # Assertion
        self.assertIsInstance(ble_devices, list)
        self.assertEqual(len(ble_devices), 0)

    @patch('dbus.SystemBus')
    @patch('dbus.Interface')
    def test_get_lte_devices_success(self, mocked_interface, _):
        # Make mocked modems
        modem0 = MagicMock()
        mocked_modems = [modem0]

        # Properties of a mocked modem with LTE capability
        mocked_modem0_properties = {
            'Model': 'QUECTEL Mobile Broadband Module',
            'Manufacturer': 'QUALCOMM INCORPORATED',
            'CurrentCapabilities': 9,
            'EquipmentIdentifier': '867698048214905',
        }

        # Set mocked modems and their properties in dbus
        mocked_interface = mocked_interface.return_value
        mocked_interface.GetManagedObjects.return_value = mocked_modems
        mocked_interface.GetAll.return_value = mocked_modem0_properties

        # Retrieve list of LTE devices
        lte_devices = get_lte_devices()

        # Assertion
        self.assertIsInstance(lte_devices, list)
        self.assertEqual(len(lte_devices), 1)
        self.assertDictEqual(lte_devices[0], {
            'Model': 'QUECTEL Mobile Broadband Module',
            'Manufacturer': 'QUALCOMM INCORPORATED',
            'EquipmentIdentifier': '867698048214905',
        })

    @patch('dbus.SystemBus')
    @patch('dbus.Interface')
    def test_get_lte_devices_missing_lte_capability(self, mocked_interface, _):
        # Make mocked modems
        modem0 = MagicMock()
        mocked_modems = [modem0]

        # Properties of a mocked modem without LTE capability
        mocked_modem0_properties = {
            'Model': 'QUECTEL Mobile Broadband Module',
            'Manufacturer': 'QUALCOMM INCORPORATED',
            'CurrentCapabilities': 0,
            'EquipmentIdentifier': '867698048214905',
        }

        # Set mocked modems and their properties in dbus
        mocked_interface = mocked_interface.return_value
        mocked_interface.GetManagedObjects.return_value = mocked_modems
        mocked_interface.GetAll.return_value = mocked_modem0_properties

        # Retrieve list of LTE devices
        lte_devices = get_lte_devices()

        # Assertion
        self.assertIsInstance(lte_devices, list)
        self.assertEqual(len(lte_devices), 0)

    @patch('dbus.SystemBus')
    @patch('dbus.Interface')
    def test_get_lte_devices_no_devices(self, mocked_interface, _):
        # Make mocked modems
        mocked_modems = []

        # Set mocked modems in dbus
        mocked_interface = mocked_interface.return_value
        mocked_interface.GetManagedObjects.return_value = mocked_modems

        # Retrieve list of LTE devices
        lte_devices = get_lte_devices()

        # Assertion
        self.assertIsInstance(lte_devices, list)
        self.assertEqual(len(lte_devices), 0)

    @patch('dbus.SystemBus')
    @patch('dbus.Interface', side_effect=DBusException('Not authorized'))
    def test_get_lte_devices_exception(self, mocked_interface, _):
        # Make mocked modems
        mocked_modems = []

        # Set mocked modems in dbus
        mocked_interface = mocked_interface.return_value
        mocked_interface.GetManagedObjects.return_value = mocked_modems

        # Retrieve list of LTE devices
        lte_devices = get_lte_devices()

        # Assertion
        self.assertIsInstance(lte_devices, list)
        self.assertEqual(len(lte_devices), 0)

    @patch('dbus.SystemBus')
    @patch('dbus.Interface')
    def test_get_wifi_devices_success_state0(self, mocked_interface, _):
        # Make mocked NetworkManager devices
        nm_device0 = MagicMock()
        mocked_nm_devices = [nm_device0]

        # Properties of a mocked NetworkManager device(WiFi)
        mocked_nm_device0_properties = {
            'Interface': 'wlx488ad22b280f',
            'Driver': 'r8188eu',
            'DriverVersion': '5.11.0-40-generic',
            'Capabilities': 1,
            'Ip4Address': 0,
            'State': 100,
            'Managed': '1',
            'Autoconnect': '1',
            'DeviceType': 2,
            'Mtu': 1500,
            'Real': '1',
            'Ip4Connectivity': 1,
            'Ip6Connectivity': 1,
            'InterfaceFlags': 0
        }

        # Set mocked NetworkManager devices and their properties in dbus
        mocked_interface = mocked_interface.return_value
        mocked_interface.GetDevices.return_value = mocked_nm_devices
        mocked_interface.GetAll.return_value = mocked_nm_device0_properties

        # Retrieve list of WiFi devices
        wifi_devices = get_wifi_devices()

        # Assertion
        self.assertIsInstance(wifi_devices, list)
        self.assertEqual(len(wifi_devices), 1)
        self.assertDictEqual(wifi_devices[0], {
            'Interface': 'wlx488ad22b280f',
            'Type': 'Wi-Fi',
            'Driver': 'r8188eu',
            'State': 'Activated',
        })

    @patch('dbus.SystemBus')
    @patch('dbus.Interface')
    def test_get_wifi_devices_success_state1(self, mocked_interface, _):
        # Make mocked NetworkManager devices
        nm_device0 = MagicMock()
        mocked_nm_devices = [nm_device0]

        # Properties of a mocked NetworkManager device(WiFi)
        mocked_nm_device0_properties = {
            'Interface': 'wlx488ad22b280f',
            'Driver': 'r8188eu',
            'DriverVersion': '5.11.0-40-generic',
            'Capabilities': 1,
            'Ip4Address': 0,
            'State': 20,
            'Managed': '1',
            'Autoconnect': '1',
            'DeviceType': 2,
            'Mtu': 1500,
            'Real': '1',
            'Ip4Connectivity': 1,
            'Ip6Connectivity': 1,
            'InterfaceFlags': 0
        }

        # Set mocked NetworkManager devices and their properties in dbus
        mocked_interface = mocked_interface.return_value
        mocked_interface.GetDevices.return_value = mocked_nm_devices
        mocked_interface.GetAll.return_value = mocked_nm_device0_properties

        # Retrieve list of WiFi devices
        wifi_devices = get_wifi_devices()

        # Assertion
        self.assertIsInstance(wifi_devices, list)
        self.assertEqual(len(wifi_devices), 1)
        self.assertDictEqual(wifi_devices[0], {
            'Interface': 'wlx488ad22b280f',
            'Type': 'Wi-Fi',
            'Driver': 'r8188eu',
            'State': 'Unavailable',
        })

    @patch('dbus.SystemBus')
    @patch('dbus.Interface')
    def test_get_wifi_devices_no_wifi_devices(self, mocked_interface, _):
        # Make mocked NetworkManager devices
        nm_device0 = MagicMock()
        mocked_nm_devices = [nm_device0]

        # Properties of a mocked NetworkManager device(Ethernet)
        mocked_nm_device0_properties = {
            'Interface': 'wlx488ad22b280f',
            'Driver': 'r8188eu',
            'DriverVersion': '5.11.0-40-generic',
            'Capabilities': 1,
            'Ip4Address': 0,
            'State': 20,
            'Managed': '1',
            'Autoconnect': '1',
            'DeviceType': 1,
            'Mtu': 1500,
            'Real': '1',
            'Ip4Connectivity': 1,
            'Ip6Connectivity': 1,
            'InterfaceFlags': 0
        }

        # Set mocked NetworkManager devices and their properties in dbus
        mocked_interface = mocked_interface.return_value
        mocked_interface.GetDevices.return_value = mocked_nm_devices
        mocked_interface.GetAll.return_value = mocked_nm_device0_properties

        # Retrieve list of WiFi devices
        wifi_devices = get_wifi_devices()

        # Assertion
        self.assertIsInstance(wifi_devices, list)
        self.assertEqual(len(wifi_devices), 0)

    @patch('dbus.SystemBus')
    @patch('dbus.Interface')
    def test_get_wifi_devices_no_nm_devices(self, mocked_interface, _):
        # Make mocked NetworkManager devices
        mocked_nm_devices = []

        # Set mocked NetworkManager devices and their properties in dbus
        mocked_interface = mocked_interface.return_value
        mocked_interface.GetDevices.return_value = mocked_nm_devices

        # Retrieve list of WiFi devices
        wifi_devices = get_wifi_devices()

        # Assertion
        self.assertIsInstance(wifi_devices, list)
        self.assertEqual(len(wifi_devices), 0)

    @patch('dbus.SystemBus')
    @patch('dbus.Interface', side_effect=DBusException('Not authorized'))
    def test_get_wifi_devices_exception(self, mocked_interface, _):
        # Make mocked NetworkManager devices
        mocked_nm_devices = []

        # Set mocked NetworkManager devices and their properties in dbus
        mocked_interface = mocked_interface.return_value
        mocked_interface.GetDevices.return_value = mocked_nm_devices

        # Retrieve list of WiFi devices
        wifi_devices = get_wifi_devices()

        # Assertion
        self.assertIsInstance(wifi_devices, list)
        self.assertEqual(len(wifi_devices), 0)

    @patch.dict('os.environ', {"VARIANT": "HNT-TEST"})
    @patch.dict('hm_pyhelper.hardware_definitions.variant_definitions', {
        "HNT-TEST": {
            "NO_KEY_STORAGE_BUS": "/dev/i2c-3",
            "SWARM_KEY_URI": ["ecc://i2c-7:96?slot=0"],
        }
    })
    @patch('hw_diag.utilities.hardware.config_search_param', return_value=True)
    def test_detect_ecc_from_SWARM_KEY_URI(
            self,
            mocked_config_search_param
    ):
        diagnostics = {
            'VA': 'HNT-TEST',
            'ECC': None,
        }
        detect_ecc(diagnostics)
        self.assertTrue(diagnostics['ECC'])
        mocked_config_search_param.assert_called_once_with('i2cdetect -y 7',
                                                           self.ECC_I2C_DETECT_PATTERN)

    @patch.dict('os.environ', {"VARIANT": "HNT-TEST"})
    @patch.dict('hm_pyhelper.hardware_definitions.variant_definitions', {
        "HNT-TEST": {
            "NO_KEY_STORAGE_BUS": "/dev/i2c-3",
            "NO_SWARM_KEY_URI": ["ecc://i2c-7:96?slot=0"],
        }
    })
    @patch('hw_diag.utilities.hardware.config_search_param', return_value=True)
    def test_detect_ecc_fall_back_to_default(
            self,
            mocked_config_search_param
    ):
        diagnostics = {
            'VA': 'HNT-TEST',
            'ECC': None,
        }
        detect_ecc(diagnostics)
        self.assertTrue(diagnostics['ECC'])
        mocked_config_search_param.assert_called_once_with('i2cdetect -y 1',
                                                           self.ECC_I2C_DETECT_PATTERN)


@patch.dict('os.environ', {"BALENA_DEVICE_TYPE": "raspberrypicm4-ioboard"})
def test_has_external_antenna_support_true():
    """Should return `True` for a CM4-based device."""

    assert has_external_antenna_support() is True


@patch.dict('os.environ', {"BALENA_DEVICE_TYPE": "raspberrypi4-64"})
def test_has_external_antenna_support_false():
    """Should return `False` for a non-CM4-based device."""

    assert has_external_antenna_support() is False


@patch('hw_diag.utilities.hardware.balena_cloud.BalenaCloud.new_from_env')
def test_is_external_antenna_no_device_var(mocked_bc_class):
    """Should create a BalenaCloud instance, retrieve the device config variables and
    return `False` due to absence of device config var."""

    mocked_bc = mocked_bc_class.return_value
    mocked_bc.get_device_config_variables.return_value = [
        {'name': 'TEST_VAR_1', 'value': 'test-value-1'},
    ]

    assert is_external_antenna_enabled() is False


@pytest.mark.parametrize('dtparam_var_name', DTPARAM_CONFIG_VAR_NAMES)
@patch('hw_diag.utilities.hardware.balena_cloud.BalenaCloud.new_from_env')
def test_is_external_antenna_no_ant2(mocked_bc_class, dtparam_var_name):
    """Should create a BalenaCloud instance, retrieve the device config variables and
    return `False` due to absence of `"ant2"` item in device config var."""

    mocked_bc = mocked_bc_class.return_value
    mocked_bc.get_device_config_variables.return_value = [
        {'name': 'TEST_VAR_1', 'value': 'test-value-1'},
        {'name': dtparam_var_name, 'value': '"item1","item2"'},
    ]

    assert is_external_antenna_enabled() is False


@pytest.mark.parametrize('dtparam_var_name', DTPARAM_CONFIG_VAR_NAMES)
@patch('hw_diag.utilities.hardware.balena_cloud.BalenaCloud.new_from_env')
def test_is_external_antenna_ant2(mocked_bc_class, dtparam_var_name):
    """Should create a BalenaCloud instance, retrieve the device config variables and
    return `True` due to presence of `"ant2"` item in device config var."""

    mocked_bc = mocked_bc_class.return_value
    mocked_bc.get_device_config_variables.return_value = [
        {'name': 'TEST_VAR_1', 'value': 'test-value-1'},
        {'name': dtparam_var_name, 'value': f'"item1",{EXT_ANT_DTPARAM},"item2"'},
    ]

    assert is_external_antenna_enabled() is True


@patch('hw_diag.utilities.hardware.balena_cloud.BalenaCloud.new_from_env')
def test_set_external_antenna_enabled_enable_existing_device_var(mocked_bc_class):
    """Should create a BalenaCloud instance, retrieve the fleet and device config variables and
    add `"ant2"` param to existing device config var, pushing it back via BalenaCloud."""

    mocked_bc = mocked_bc_class.return_value
    mocked_bc.get_device_config_variables.return_value = [
        {'name': 'TEST_VAR_1', 'value': 'test-value-1', 'id': 10},
        {
            'name': DTPARAM_CONFIG_VAR_NAMES[0],
            'value': '"item1","item2"',
            'id': 20
        },
    ]
    mocked_bc.get_fleet_config_variables.return_value = [
        {'name': 'TEST_VAR_1', 'value': 'test-value-1', 'id': 30},
        {
            'name': DTPARAM_CONFIG_VAR_NAMES[0],
            'value': '"item3","item4"',
            'id': 40
        },
    ]

    set_external_antenna_enabled(True)

    mocked_bc.update_device_config_variable.assert_called_once_with(
        20, f'"item1","item2",{EXT_ANT_DTPARAM}'
    )
    mocked_bc.create_device_config_variable.assert_not_called()


@patch('hw_diag.utilities.hardware.balena_cloud.BalenaCloud.new_from_env')
def test_set_external_antenna_enabled_enable_new_device_var(mocked_bc_class):
    """Should create a BalenaCloud instance, retrieve the fleet and device config variables and
    create new device var from fleet var and `"ant2" param`, pushing it back via BalenaCloud."""

    mocked_bc = mocked_bc_class.return_value
    mocked_bc.get_device_config_variables.return_value = [
        {'name': 'TEST_VAR_1', 'value': 'test-value-1', 'id': 10},
        {'name': 'TEST_VAR_2', 'value': 'test-value-2', 'id': 20},
    ]
    mocked_bc.get_fleet_config_variables.return_value = [
        {'name': 'TEST_VAR_1', 'value': 'test-value-1', 'id': 30},
        {
            'name': DTPARAM_CONFIG_VAR_NAMES[0],
            'value': '"item3","item4"',
            'id': 40
        },
    ]

    set_external_antenna_enabled(True)

    mocked_bc.update_device_config_variable.assert_not_called()
    mocked_bc.create_device_config_variable.assert_called_once_with(
        DTPARAM_CONFIG_VAR_NAME,
        f'"item3","item4",{EXT_ANT_DTPARAM}'
    )


@patch('hw_diag.utilities.hardware.balena_cloud.BalenaCloud.new_from_env')
@patch('hw_diag.utilities.hardware.logging')
def test_set_external_antenna_enabled_enable_already_enabled(mocked_logging, mocked_bc_class):
    """Should create a BalenaCloud instance, retrieve the fleet and device config variables and
    return right away with already enabled log message, due to presence of `"ant2"` item in device
    config var."""

    mocked_bc = mocked_bc_class.return_value
    mocked_bc.get_device_config_variables.return_value = [
        {'name': 'TEST_VAR_1', 'value': 'test-value-1', 'id': 10},
        {
            'name': DTPARAM_CONFIG_VAR_NAMES[0],
            'value': f'"item1",{EXT_ANT_DTPARAM},"item2"',
            'id': 20
        },
    ]
    mocked_bc.get_fleet_config_variables.return_value = [
        {'name': 'TEST_VAR_1', 'value': 'test-value-1', 'id': 30},
        {
            'name': DTPARAM_CONFIG_VAR_NAMES[0],
            'value': '"item3","item4"',
            'id': 40
        },
    ]

    set_external_antenna_enabled(True)

    mocked_bc.update_device_config_variable.assert_not_called()
    mocked_bc.create_device_config_variable.assert_not_called()
    mocked_logging.info.assert_called_with('External antenna already enabled')


@patch('hw_diag.utilities.hardware.balena_cloud.BalenaCloud.new_from_env')
def test_set_external_antenna_enabled_disable(mocked_bc_class):
    """Should create a BalenaCloud instance, retrieve the fleet and device config variables and
    remove `"ant2"` param from existing device config var, pushing it back via BalenaCloud."""

    mocked_bc = mocked_bc_class.return_value
    mocked_bc.get_device_config_variables.return_value = [
        {'name': 'TEST_VAR_1', 'value': 'test-value-1', 'id': 10},
        {
            'name': DTPARAM_CONFIG_VAR_NAMES[0],
            'value': f'"item1",{EXT_ANT_DTPARAM},"item2"',
            'id': 20
        },
    ]
    mocked_bc.get_fleet_config_variables.return_value = [
        {'name': 'TEST_VAR_1', 'value': 'test-value-1', 'id': 30},
        {
            'name': DTPARAM_CONFIG_VAR_NAMES[0],
            'value': '"item3","item4"',
            'id': 40
        },
    ]

    set_external_antenna_enabled(False)

    mocked_bc.update_device_config_variable.assert_called_once_with(20, '"item1","item2"')
    mocked_bc.create_device_config_variable.assert_not_called()


@patch('hw_diag.utilities.hardware.balena_cloud.BalenaCloud.new_from_env')
@patch('hw_diag.utilities.hardware.logging')
def test_set_external_antenna_enabled_disable_already_disabled_no_device_var(
    mocked_logging, mocked_bc_class
):
    """Should create a BalenaCloud instance, retrieve the fleet and device config variables and
    return right away with already disabled log message, due to absence if device config var."""

    mocked_bc = mocked_bc_class.return_value
    mocked_bc.get_device_config_variables.return_value = [
        {'name': 'TEST_VAR_1', 'value': 'test-value-1', 'id': 10},
        {'name': 'TEST_VAR_2', 'value': 'test-value-2', 'id': 20},
    ]
    mocked_bc.get_fleet_config_variables.return_value = [
        {'name': 'TEST_VAR_1', 'value': 'test-value-1', 'id': 30},
        {
            'name': DTPARAM_CONFIG_VAR_NAMES[0],
            'value': '"item3","item4"',
            'id': 40
        },
    ]

    set_external_antenna_enabled(False)

    mocked_bc.update_device_config_variable.assert_not_called()
    mocked_bc.create_device_config_variable.assert_not_called()
    mocked_logging.info.assert_called_with('External antenna already disabled')


@patch('hw_diag.utilities.hardware.balena_cloud.BalenaCloud.new_from_env')
@patch('hw_diag.utilities.hardware.logging')
def test_set_external_antenna_enabled_disable_already_disabled_no_device_param(
    mocked_logging, mocked_bc_class
):
    """Should create a BalenaCloud instance, retrieve the fleet and device config variables and
    return right away with already disabled log message, due to absence of `"ant2"` item in device
    config var."""

    mocked_bc = mocked_bc_class.return_value
    mocked_bc.get_device_config_variables.return_value = [
        {'name': 'TEST_VAR_1', 'value': 'test-value-1', 'id': 10},
        {
            'name': DTPARAM_CONFIG_VAR_NAMES[0],
            'value': '"item1","item2"',
            'id': 20
        },
    ]
    mocked_bc.get_fleet_config_variables.return_value = [
        {'name': 'TEST_VAR_1', 'value': 'test-value-1', 'id': 30},
        {
            'name': DTPARAM_CONFIG_VAR_NAMES[0],
            'value': '"item3","item4"',
            'id': 40
        },
    ]

    set_external_antenna_enabled(False)

    mocked_bc.update_device_config_variable.assert_not_called()
    mocked_bc.create_device_config_variable.assert_not_called()
    mocked_logging.info.assert_called_with('External antenna already disabled')
