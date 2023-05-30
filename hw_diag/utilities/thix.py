import requests


THIX_FORWARDER_API = 'http://thix-forwarder:8080/v1'


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
