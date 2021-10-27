# hm-diag: Helium Miner Diagnostics Container

**hm-diag** is a small website that displays diagnostic information about a hotspot.
The website is only accessible if you are on the same network as the hotspot.
Some people have exposed their devices publicly but this is not generally advised.

## Quick start

Find the IP address of the hotspot using Balena's dashboard or network scanner.
The website is available on port `80` so you can simply input the hotspot's
IP address in the browser.

## Diagnostics JSON Layout

As part of the code the system produces a JSON file which then is used to carry the data over easily to other parts of the system.

| Variable | Description |
| --- | --- |
| AN | The Animal Name of the miner |
| APPNAME | The name advertised on BTLE |
| BA | Balena Application Name |
| BCH | Current blockchain height |
| BN | Balena Name, used to identify on balena |
| BSP | Sync percentage |
| BT | If the bluetooth module is detected |
| BUTTON | The GPIO pin of the button on the miner |
| CELLULAR | Whether the device has optional cellular capability |
| E0 | MAC Address of the ETH0 interface |
| ECC | If the ECC Key is detected over I2C |
| ECCOB | If the miner should have an ECC chip on board |
| FR | The hardware frequency |
| FRIENDLY | The Friendly name of the hotspot |
| FW | Firmware running on the unit |
| ID | Balena UUID |
| LOR | If a fault has been found with the LoRa Module |
| LTE | If the LTE Module is detected |
| MAC | Which mac address to print on labels in production |
| MC | If the miner is connected to the Helium Network |
| MD | If the miner is "Dialable" on the network |
| MH | The sync height of the miner |
| MN | NAT Type of the miner |
| MR | Whether the miner is relayed or not |
| MS | If miner is synced within 500 blocks |
| OK | The onboarding key of the miner |
| PF | If overall diagnostics have passed |
| PK | The public key of the miner |
| RE | The detected region plan from the miner (or override) |
| RESET | The reset pin to use for the LoRa Module |
| RPI | The serial number of the onboard Raspberry Pi or other SBC |
| SPIBUS | The SPI Bus to use for the LoRa Module |
| STATUS | The GPIO Pin of the status LED |
| TYPE | If it is a Full or Light Hotspot |
| VA | ID of the [hardware variant](https://github.com/NebraLtd/hm-pyhelper/blob/master/hm_pyhelper/hardware_definitions.py) |
| W0 | Mac Address of the WLAN0 interface |
| last_updated | When this JSON was last updated (UTC timezone) |

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

### Testing

```
pip install -r test-requirements.txt
pytest
flake8 hw_diag
```

### Deprecated deployment
This is no longer [the recommended way](https://www.balena.io/docs/learn/deploy/deployment/#overview) of doing Balena deployments.

* Add the remote Balena repo:`git remote add balena BALENA_USERNAME@git.balena-cloud.com:BALENA_USERNAME/BALENA_PROJECT.git`
* Deploy changes: `git push balena YourLocalBranch:master`

## Access from other networks

Balena will generate a public URL for a device if [PUBLIC DEVICE URL](https://www.balena.io/docs/learn/manage/actions/#enable-public-device-url) is toggled from the Balena device dashboard. This is not generally recommended, except for debugging.

## Pre built containers

This repo automatically builds docker containers and uploads them to two repositories for easy access:
- [hm-diag on DockerHub](https://hub.docker.com/r/nebraltd/hm-diag)
- [hm-diag on GitHub Packages](https://github.com/NebraLtd/hm-diag/pkgs/container/hm-diag)

The images are tagged using the docker long and short commit SHAs for that release. The current version deployed to miners can be found in the [helium-miner-software repo](https://github.com/NebraLtd/helium-miner-software/blob/production/docker-compose.yml).
