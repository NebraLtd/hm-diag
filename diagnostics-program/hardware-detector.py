# Detects all the hardware and responds them for diagnostics json

# Pin Definitions

# Stores the SPI bus to be used, the reset pin,
# and the network interface mac to use.

variant_definitions = {
# Nebra Indoor Hotspot
"NEB-IN" : {
    'spibus': 'spidev1.2',
    'reset' : 38,
    'mac' : 'eth0',
    'fcc-id' : '2AZDM-HNTIN',
    'ic-id': '27187-HNTIN'
    },
# Nebra Outdoor Hotspot
"NEB-OUT" : {
    'spibus': 'spidev1.2',
    'reset' : 38,
    'mac' : 'eth0',
    'fcc-id' : '2AZDM-HNTOUT',
    'ic-id': '27187-HNTOUT'
    },
# Nebra Light Pi Zero SPI Hotspot
"NEB-LITE-PZW-SPI" : {
    'spibus': 'spidev1.2',
    'reset' : 22,
    'mac' : 'wlan0',
    'fcc-id' : '2AZDM-HNTPZI',
    'ic-id': '27187-HNTPZI'
    },
# Nebra Light Pi Zero USB Hotspot
"NEB-LITE-PZW-USB" : {
    'spibus': 'spidev1.2',
    'reset' : 22,
    'mac' : 'wlan0',
    'fcc-id' : '2AZDM-HNTPZX',
    'ic-id': '27187-HNTPZX'
    },
# Nebra Light Pocket Beaglebone USB Hotspot
"NEB-LITE-PBB" : {
    'spibus': 'spidev0.0',
    'reset' : 1,
    'mac' : 'eth0',
    'fcc-id' : '2AZDM-HNTPBU',
    'ic-id': '27187-HNTPBU'
    }
# Original Helium Hotspot
#"HELIUM-HOTSPOT" : {'spibus': 'spidev0.0', 'reset' : 42, 'mac' : 'wlan0'},
# RAK Hotspot
#"RAK-HOTSPOT" : {'spibus': 'spidev0.0', 'reset' : 42, 'mac' : 'wlan0'},
# Syncrobit Hotspot
#"SYNCROBIT" : {'spibus': 'spidev0.0', 'reset' : 42, 'mac' : 'wlan0'}
}

# List of USB Wi-Fi Adaptors used

usb_wifi_adaptor_ids = {
"148f:5370" : "RT5370"
}

# List of LTE adaptor combinations

lte_adaptor_ids = {
"2c7c:0125" : "QUECTEL-EC25"
}
