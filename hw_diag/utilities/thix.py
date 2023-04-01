import requests
import h3


THIX_FORWARDER_API = 'http://thix-forwarder:8080/v1'


def get_unknown_gateways():
    resp = requests.get('%s/gateways/unknown' % THIX_FORWARDER_API)
    return resp.json()


def get_gateways():
    resp = requests.get('%s/gateways' % THIX_FORWARDER_API)
    return resp.json()


def submit_onboard(gateway, wallet):
    req_body = {
        'localId': gateway,
        'owner': wallet,
        'pushToThingsIX': True
    }
    resp = requests.post(
        '%s/gateways/onboard' % THIX_FORWARDER_API,
        json=req_body
    )
    if resp.status_code in [200, 201]:
        return resp.json()
    else:
        raise Exception('Invalid onboard request')


def convert_h3_to_lat_lon(h3_location):
    geo = h3.h3_to_geo(h3_location)
    return {
        'latitude': geo[0],
        'longitude': geo[1]
    }
