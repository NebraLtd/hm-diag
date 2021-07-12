# hm-diag
Helium Miner Diagnostics

# Diagnostics JSON Layout

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



## Local development environment

Because the stack is tightly intertwined with Balena, the easiest way to test the code base on your own Raspberry Pi in your own Balena project.

* Create a new Balena project for Raspberry Pi 3 (64 Bit)
* Download and flash out the disk image provided and boot the device
* Add the remote Balena repo (`git remote add balena YourUser@git.balena-cloud.com:YourUser/YourProject.git`)

You can now push your changes using the following command:

```
$ git push balena YourLocalBranch:master
```
