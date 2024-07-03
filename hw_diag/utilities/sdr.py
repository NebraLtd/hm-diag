import os


SDR_SEARCH_STRINGS = [
    "rtl283"
]


def detect_sdr():
    found_sdr = False

    for search_string in SDR_SEARCH_STRINGS:
        output = os.popen(
            '/usr/bin/lsusb | grep -i %s | wc -l' % search_string
        ).read().strip()  # nosec
        if int(output) > 0:
            found_sdr = True

    return found_sdr
