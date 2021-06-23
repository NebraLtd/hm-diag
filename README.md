# hm-diag
Helium Miner Diagnostics

# Diagnostics Json Layout

As part of the code the system produces a JSON file which then is used to carry the data over easily to other parts.

| Variable | Description |
| --- | --- |
| ECC | If the ECC Key is detected over I2C |
| E0 | MAC Address of the ETH0 interface |
| W0 | Mac Address of the WLAN0 interface |
| BN | Balena Name, used to identify on balena |
| ID | Balena UUID |
| BA | Balena Application Name |
| FR | The hardware frequency |
| FW | Firmware running on the unit |
| VA | ID Of the hardware Variant |
| RPI | The serial number of the onboard Raspberry Pi |
| BT | If the bluetooth module is detected |
| LTE | If the LTE Module is detected |
| LOR | If a fault has been found with the LoRa Module |
| PK | The public key of the miner |
| OK | The Onboarding key of the miner |
| AN | The Animal Name of the miner |
| MC | If the miner is connected to the Helium Network |
| MD | If the miner is "Dialable" on the network |
| MH | The Sync height of the miner |
| MN | NAT Type of the miner |
| RE | The detected region plan from the miner |
| PF | If Overall diagnostics have passed |
| FRIENDLY | The Friendly name of the hotspot |
| APPNAME | The name advertised on BTLE |
| SPIBUS | The SPI Bus to use for the LoRa Module |
| RESET | The reset pin to use for the LoRa Module |
| MAC | Which mac address to print on labels in production |
| STATUS | The GPIO Pin of the status LED |
| BUTTON | The GPIO pin of the button on the miner |
| ECCOB | If the miner should have an ECC chip on board |
| TYPE | If it is a Full or Light Hotspot |
