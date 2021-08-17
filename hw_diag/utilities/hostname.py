import os
import requests

from hw_diag.utilities.hardware import get_mac_addr

def set_hostname():
    """
    Sets the hostname of the miner to nebra-<last 6 of mac>
    via the balena supervisor api
    """
    path = "/sys/class/net/eth0/address"
    eth0 = get_mac_addr(path).replace(':','').lower()
    length = len(eth0)
    supervisor_addr = os.environ.get('BALENA_SUPERVISOR_ADDRESS')
    api_key = os.environ.get('BALENA_SUPERVISOR_API_KEY')

    headers = {
        'Content-Type': 'application/json',
    }
    params = (
        ('apikey', api_key),
    )
    data = '{{"network": {{"hostname": "nebra-{}"}}}}'.format(eth0[length - 6:])
    response = requests.patch(supervisor_addr + '/v1/device/host-config', headers=headers, params=params, data=data)

    return response
