variant_definitions = {
    # Nebra Indoor Hotspot Gen1
    'NEBHNT-IN1': {
        'FRIENDLY': 'Nebra Indoor Hotspot Gen 1',
        'APPNAME': 'Indoor',
        'SPIBUS': 'spidev1.2',
        'RESET': 38,
        'MAC': 'eth0',
        'STATUS': 25,
        'BUTTON': 26,
        'ECCOB': True,
        'TYPE': 'Full'
        },

    # Nebra Indoor Hotspot, Old identifier
    'Indoor': {
        'FRIENDLY': 'Nebra Indoor Hotspot Gen 1',
        'APPNAME': 'Indoor',
        'SPIBUS': 'spidev1.2',
        'RESET': 38,
        'MAC': 'eth0',
        'STATUS': 25,
        'BUTTON': 26,
        'ECCOB': True,
        'TYPE': 'Full'
        },

    # Nebra Outdoor Hotspot Gen1
    'NEBHNT-OUT1': {
        'FRIENDLY': 'Nebra Outdoor Hotspot Gen 1',
        'APPNAME': 'Outdoor',
        'SPIBUS': 'spidev1.2',
        'RESET': 38,
        'MAC': 'eth0',
        'STATUS': 25,
        'BUTTON': 26,
        'ECCOB': True,
        'TYPE': 'Full'
        },

    # Nebra Outdoor Hotspot Old Identifier
    'Outdoor': {
        'FRIENDLY': 'Nebra Outdoor Hotspot Gen 1',
        'APPNAME': 'Outdoor',
        'SPIBUS': 'spidev1.2',
        'RESET': 38,
        'MAC': 'eth0',
        'STATUS': 25,
        'BUTTON': 26,
        'ECCOB': True,
        'TYPE': 'Full'
        },

    # Nebra Pi 0 Light Hotspot SPI Ethernet
    'NEBHNT-LGT-ZS': {
        'FRIENDLY': 'Nebra Pi 0 Light Hotspot SE',
        'APPNAME': 'Pi 0 Light',
        'SPIBUS': 'spidev1.2',
        'RESET': 22,
        'MAC': 'wlan0',
        'STATUS': 24,
        'BUTTON': 23,
        'ECCOB': True,
        'TYPE': 'Full'
        },

    # Nebra Pi 0 Light Hotspot USB Ethernet
    'NEBHNT-LGT-ZX': {
        'FRIENDLY': 'Nebra Pi 0 Light Hotspot XE',
        'APPNAME': 'Pi 0 Light',
        'SPIBUS': 'spidev1.2',
        'RESET': 22,
        'MAC': 'wlan0',
        'STATUS': 24,
        'BUTTON': 23,
        'ECCOB': True,
        'TYPE': 'Full'
        },

    # Nebra Beaglebone Light Hotspot
    'NEBHNT-BBB': {
        'FRIENDLY': 'Nebra Beaglebone Light Hotspot',
        'APPNAME': 'Beaglebone Light',
        'SPIBUS': 'spidev1.0',
        'RESET': 60,
        'MAC': 'eth0',
        'STATUS': 31,
        'BUTTON': 30,
        'ECCOB': True,
        'TYPE': 'Full'
        },

    # Nebra Pocket Beagle Light Hotspot
    'NEBHNT-PBB': {
        'FRIENDLY': 'Nebra Pocket Beagle Light Hotspot',
        'APPNAME': 'PB Light',
        'SPIBUS': 'spidev1.2',
        'RESET': 60,
        'MAC': 'wlan0',
        'STATUS': 31,
        'BUTTON': 30,
        'ECCOB': True,
        'TYPE': 'Full'
        },

    # Nebra Hotspot HAT Rockpi 4
    'NEBHNT-HHRK4': {
        'FRIENDLY': 'Nebra Hotspot HAT RockPi 4',
        'APPNAME': 'RockPi',
        'SPIBUS': 'spidev1.0',
        'RESET': 149,
        'MAC': 'eth0',
        'STATUS': 156,
        'BUTTON': 154,
        'ECCOB': True
        },

    # Nebra Hotspot HAT RPi 3/4 Full
    'NEBHNT-HHRPI': {
        'FRIENDLY': 'Nebra Hotspot HAT RPi',
        'APPNAME': 'RPi',
        'SPIBUS': 'spidev0.0',
        'RESET': 22,
        'MAC': 'eth0',
        'STATUS': 24,
        'BUTTON': 23,
        'ECCOB': True
        },

    # Nebra Hotspot HAT RPi Light
    'NEBHNT-HHRPL': {
        'FRIENDLY': 'Nebra Hotspot HAT RPi Light',
        'APPNAME': 'Light RPi',
        'SPIBUS': 'spidev0.0',
        'RESET': 22,
        'MAC': 'eth0',
        'STATUS': 24,
        'BUTTON': 23,
        'ECCOB': True
        },

    # Nebra Hotspot HAT Tinkerboard 1
    'NEBHNT-HHTK': {
        'FRIENDLY': 'Nebra Hotspot HAT Tinkerboard Light',
        'APPNAME': 'Tinkerboard Light',
        'SPIBUS': 'spidev2.0',
        'RESET': 167,
        'MAC': 'eth0',
        'STATUS': 163,
        'BUTTON': 162,
        'ECCOB': True,
        'TYPE': 'Light'
        },

    # Nebra Hotspot HAT Tinkerboard 2
    'NEBHNT-HHTK2': {
        'FRIENDLY': 'Nebra Hotspot HAT Tinkerboard 2',
        'APPNAME': 'Tinkerboard',
        'SPIBUS': 'spidev2.0',
        'RESET': 167,
        'MAC': 'eth0',
        'STATUS': 163,
        'BUTTON': 162,
        'ECCOB': True,
        'TYPE': 'Full'
        },

    # RAKwireless Hotspot Miner
    'COMP-RAKHM': {
        'FRIENDLY': 'RAK Hotspot Miner',
        'SPIBUS': 'spidev0.0',
        'RESET': 17,
        'MAC': 'wlan0',
        'STATUS': 20,
        'BUTTON': 21,
        'ECCOB': True,
        'TYPE': 'Full'
        },

    # Helium Hotspot
    'COMP-HELIUM': {
        'FRIENDLY': 'OG Helium Hotspot',
        'SPIBUS': 'spidev0.0',
        'RESET': 17,
        'MAC': 'wlan0',
        'STATUS': 20,
        'BUTTON': 21,
        'ECCOB': True,
        'TYPE': 'Full'
        },

    # DIY Pi Supply Hotspot HAT
    'DIY-PISLGH': {
        'FRIENDLY': 'DIY Pi Supply Hotspot HAT',
        'SPIBUS': 'spidev0.0',
        'RESET': 22,
        'MAC': 'eth0',
        'STATUS': 20,
        'BUTTON': 21,
        'ECCOB': False,
        'TYPE': 'Light'
        },

    # Nebra Indoor Hotspot
    'DIY-RAK2287': {
        'FRIENDLY': 'DIY RAK2247/RAK2287 HAT',
        'SPIBUS': 'spidev0.0',
        'RESET': 17,
        'MAC': 'eth0',
        'STATUS': 20,
        'BUTTON': 21,
        'ECCOB': False,
        'TYPE': 'Light'
        }
}
