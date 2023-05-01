"Constants used by hm-diag"

from pathlib import Path
from dataclasses import dataclass

HPT_IP = '192.168.220.1'  # NOSONAR
MANUFACTURING_MODE_FILE_LOCATION = Path('/var/nebra/in_manufacturing')
MANUFACTURING_MODE_ENV_VAR = 'IN_MANUFACTURING'


@dataclass(frozen=True)
class DIAG_JSON_KEYS:
    ECC_STATUS: str = "ECC"
    ETH_MAC_ADDRESS: str = "E0"
    WLAN_MAC_ADDRESS: str = "W0"
    BALENA_DEVICE_NAME: str = "BN"
    BALENA_UUID: str = "ID"
    BALENA_FLEET_NAME: str = "BA"
    FREQUENCY: str = "FR"
    FIRMWARE_VERSION: str = "FW"
    VARIANT: str = "VA"
    SERIAL_NUMBER: str = "serial_number"
    BLUETOOTH_STATUS: str = "BT"
    LTE_STATUS: str = "LTE"
    LORA_STATUS: str = "LOR"
    PUBLIC_KEY: str = "PK"
    ONBOARDING_KEY: str = "OK"
    HELIUM_ANIMLA_NAME: str = "AN"
    REGION: str = "RE"
    DEVICE_OVERALL_STATUS: str = "PF"
    FRIENDLY_NAME: str = "FRIENDLY"
    BALENA_APP_NAME: str = "APPNAME"
    SPID_BUS: str = "SPIBUS"
    RESET_PIN: str = "RESET"
    ETHERNET_DEVICE_NAME: str = "MAC"
    STATUS_LED_PIN: str = "STATUS"
    BUTTON_PIN: str = "BUTTON"
    ECC_ONBBOARDED: str = "ECCOB"
    MINER_TYPE: str = "TYPE"
