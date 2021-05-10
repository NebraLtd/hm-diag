# Detects all the hardware and responds them for diagnostics json

# Pin Definitions

# Stores the SPI bus to be used, the reset pin,
# and the network interface mac to use.

variant_definitions = {
    # Nebra Indoor Hotspot Gen1
    "NEBHNT-IN1" : {
        'spibus': 'spidev1.2',
        'reset' : 38,
        'mac' : 'eth0',
        'status': 25,
        'button': 26,
        'ecc': True,
        'type': "Full"
        },

    # Nebra Outdoor Hotspot Gen1
    "NEBHNT-OUT1" : {
        'spibus': 'spidev1.2',
        'reset' : 38,
        'mac' : 'eth0',
        'status': 25,
        'button': 26,
        'ecc': True,
        'type': "Full"
        },

    # Nebra Pi 0 Light Hotspot SPI Ethernet
    "NEBHNT-LGT-ZS" : {
        'spibus': 'spidev1.2',
        'reset' : 22,
        'mac' : 'wlan0',
        'status': 24,
        'button': 23,
        'ecc': True,
        'type': "Full"
        },

    # Nebra Pi 0 Light Hotspot USB Ethernet
    "NEBHNT-LGT-ZX" : {
        'spibus': 'spidev1.2',
        'reset' : 22,
        'mac' : 'wlan0',
        'status': 24,
        'button': 23,
        'ecc': True,
        'type': "Full"
        },

    # Nebra Beaglebone Light Hotspot
    "NEBHNT-BBB" : {
        'spibus': 'spidev1.0',
        'reset' : 60,
        'mac' : 'eth0',
        'status': 31,
        'button': 30,
        'ecc': True,
        'type': "Full"
        },

    # Nebra Pocket Beagle Light Hotspot
    "NEBHNT-PBB" : {
        'spibus': 'spidev1.2',
        'reset' : 60,
        'mac' : 'wlan0',
        'status': 31,
        'button': 30,
        'ecc': True,
        'type': "Full"
        },

    # Nebra Hotspot HAT Rockpi 4
    "NEBHNT-HHRK4" : {
        'spibus': 'spidev1.0',
        'reset' : 149,
        'mac' : 'eth0',
        'status': 156,
        'button': 154,
        'ecc': True
        },

    # Nebra Hotspot HAT RPi 3/4 Full
    "NEBHNT-HHRPI" : {
        'spibus': 'spidev0.0',
        'reset' : 22,
        'mac' : 'eth0',
        'status': 24,
        'button': 23,
        'ecc': True
        },

    # Nebra Hotspot HAT RPi Light
    "NEBHNT-HHRPL" : {
        'spibus': 'spidev0.0',
        'reset' : 22,
        'mac' : 'eth0',
        'status': 24,
        'button': 23,
        'ecc': True
        },

    # Nebra Hotspot HAT Tinkerboard 1
    "NEBHNT-HHTK" : {
        'spibus': 'spidev2.0',
        'reset' : 167,
        'mac' : 'eth0',
        'status': 163,
        'button': 162,
        'ecc': True,
        'type': "Light"
        },

    # Nebra Hotspot HAT Tinkerboard 2
    "NEBHNT-HHTK2" : {
        'spibus': 'spidev2.0',
        'reset' : 167,
        'mac' : 'eth0',
        'status': 163,
        'button': 162,
        'ecc': True,
        'type': "Full"
        },

    # RAKwireless Hotspot Miner
    "COMP-RAKHM" : {
        'spibus': 'spidev0.0',
        'reset' : 17,
        'mac' : 'wlan0',
        'status': 20,
        'button': 21,
        'ecc': True,
        'type': "Full"
        },

    # Helium Hotspot
    "COMP-HELIUM" : {
        'spibus': 'spidev0.0',
        'reset' : 17,
        'mac' : 'wlan0',
        'status': 20,
        'button': 21,
        'ecc': True,
        'type': "Full"
        },

    # DIY Pi Supply Hotspot HAT
    "DIY-PISLGH" : {
        'spibus': 'spidev0.0',
        'reset' : 22,
        'mac' : 'eth0',
        'status': 20,
        'button': 21,
        'ecc': False,
        'type': "Light"
        },

    # Nebra Indoor Hotspot
    "DIY-RAK2287" : {
        'spibus': 'spidev0.0',
        'reset' : 17,
        'mac' : 'eth0',
        'status': 20,
        'button': 21,
        'ecc': False,
        'type': "Light"
        }
}

# List of USB Wi-Fi Adaptors used

usb_wifi_adaptor_ids = {
    "148f:5370" : "RT5370"
}

# List of LTE adaptor combinations

lte_adaptor_ids = {
    "2c7c:0125" : "QUECTEL-EC25"
}
