import requests
import os
import shutil


THIX_FORWARDER_API = 'http://thix-forwarder:8080/v1'


def is_region_set():
    return os.path.isfile('/var/pktfwd/region')


def write_region_file(region):
    with open("/var/pktfwd/region", "w") as region_file:
        region_file.write(region)


def get_unknown_gateways():
    resp = requests.get('%s/gateways/unknown' % THIX_FORWARDER_API)  # nosec
    return resp.json()


def get_gateways():
    resp = requests.get('%s/gateways' % THIX_FORWARDER_API)  # nosec

    try:
        onboarded_gw = resp.json().get('onboarded')[0]
        gw_id = onboarded_gw.get('localId')
        requests.get('%s/gateways/%s/sync' % (THIX_FORWARDER_API, gw_id))  # nosec
        resp = requests.get('%s/gateways' % THIX_FORWARDER_API)  # nosec
    except Exception:  # nosec
        pass

    return resp.json()


def submit_onboard(gateway, wallet):
    req_body = {
        'localId': gateway,
        'owner': wallet,
        'pushToThingsIX': True
    }
    resp = requests.post(  # nosec
        '%s/gateways/onboard' % THIX_FORWARDER_API,
        json=req_body
    )
    if resp.status_code in [200, 201]:
        return resp.json()
    else:
        raise Exception('Invalid onboard request')


def remove_testnet():
    try:
        shutil.rmtree('/var/thix/')
    except Exception:  # nosec
        pass
