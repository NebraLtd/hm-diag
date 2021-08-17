# hm-diag
Helium Miner Diagnostics

**hm-diag** is a small website that displays diagnostic information about a hotspot.
The website is only accessible if you are on the same network as the hotspot.
Some people have exposed their devices publicly but this is not generally advised.

## Quick start

Find the IP address of the hotspot using Balena's dashboard or network scanner.
The website is available on port `80` so you can simply input the hotspot's
IP address in the browser.

## Diagnostics JSON Layout

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

* Create a new Balena application (in a personal org):
    * Default device type: `Raspberry Pi 3 (using 64 bit OS)`
    * Application type: `Starter`
* Add a device:
    * Select newest version
    * Development (required for local mode)
    * Click `Download Balena OS`
* Use [Etcher](https://www.balena.io/etcher/) to flash the downloaded image
* Insert flash drive into the Raspberry Pi and boot (don't forget to plugin ethernet if necessary)
* Set env vars for the application in Balena:
    * `FREQ`: 868, 915, etc.
    * `VARIANT`: Choose from [here](https://github.com/NebraLtd/helium-hardware-definitions/blob/master/src/hm_hardware_defs/variant.py)
* Deploy changes to:
    * All devices in application: `balena push BALENA_APPLICATION`
    * Single device in local mode: `balena push UUID.local` (this will build on the device and )

If you are on the same network as the Raspberry Pi, enter `LOCAL IP ADDRESS` from Balena into the browser.

### Deprecated deployment
This is no longer [the recommended way](https://www.balena.io/docs/learn/deploy/deployment/#overview) of doing Balena deployments.

* Add the remote Balena repo:`git remote add balena BALENA_USERNAME@git.balena-cloud.com:BALENA_USERNAME/BALENA_PROJECT.git`
* Deploy changes: `git push balena YourLocalBranch:master`

## Access from other networks

Balena will generate a public URL for a device if [PUBLIC DEVICE URL](https://www.balena.io/docs/learn/manage/actions/#enable-public-device-url) is toggled from the Balena device dashboard. This is not generally recommended, except for debugging.
