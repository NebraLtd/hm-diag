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

    # Nebra Hotspot HAT Tinkerboard
    "NEBHNT-HHTK" : {
        'spibus': 'spidev1.2',
        'reset' : 38,
        'mac' : 'eth0',
        'status': 25,
        'button': 26,
        'ecc': True,
        'type': "Full"
        },

    # Nebra Hotspot HAT Tinkerboard
    "NEBHNT-HHTK2" : {
        'spibus': 'spidev1.2',
        'reset' : 38,
        'mac' : 'eth0',
        'status': 25,
        'button': 26,
        'ecc': True,
        'type': "Full"
        },

    # Nebra Indoor Hotspot
    "NEBHNT-IN1" : {
        'spibus': 'spidev1.2',
        'reset' : 38,
        'mac' : 'eth0',
        'status': 25,
        'button': 26,
        'ecc': True,
        'type': "Full"
        },

    # Nebra Indoor Hotspot
    "NEBHNT-IN1" : {
        'spibus': 'spidev1.2',
        'reset' : 38,
        'mac' : 'eth0',
        'status': 25,
        'button': 26,
        'ecc': True,
        'type': "Full"
        },

    # Nebra Indoor Hotspot
    "NEBHNT-IN1" : {
        'spibus': 'spidev1.2',
        'reset' : 38,
        'mac' : 'eth0',
        'status': 25,
        'button': 26,
        'ecc': True,
        'type': "Full"
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
