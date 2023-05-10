import requests
import json
import logging
from collections import namedtuple
from urllib.parse import urlencode, urlunparse, urlparse

from hw_diag.utilities.db import get_value, set_value
from hw_diag.utilities.hardware import is_nebra_device
from hw_diag.utilities.diagnostics import cached_diagnostics_data
from hw_diag.constants import DIAG_JSON_KEYS

THIRD_PARTY_MINER_REGISTRATION_URL = \
    "https://dashboard.nebra.com/api/v0.1/register-third-party-hotspot"
MINER_CLAIM_URL = "https://dashboard.nebra.com/devices/#qr-modal"
REGISTERED_KEY = "is_registered"

log = logging.getLogger()
log.setLevel(logging.DEBUG)


def get_value_noexcept(key: str, default: str | None = None) -> str | None:
    '''get value if exits otherwise default value'''
    try:
        return get_value(key)
    except Exception as e:
        logging.debug(f"exception while retrieving {key}: {e}, using default")
        return default


def set_value_noexcept(key: str, value: str) -> bool:
    '''return true if value can be set in db without error'''
    try:
        set_value(key, value)
    except Exception as e:
        logging.error(f"failed to set value {e}")
        return False


def is_registered() -> bool:
    return get_value_noexcept(REGISTERED_KEY) == 'True'


def set_registered(state: bool):
    set_value_noexcept(REGISTERED_KEY, str(state))


def _prepare_registration_payload(diagnostics: dict) -> dict:
    device_payload = {
        "ethernet_mac_address": diagnostics[DIAG_JSON_KEYS.ETH_MAC_ADDRESS],
        "wifi_mac_address":  diagnostics[DIAG_JSON_KEYS.WLAN_MAC_ADDRESS],
        "frequency": diagnostics[DIAG_JSON_KEYS.FREQUENCY],
        "balena_uuid": diagnostics[DIAG_JSON_KEYS.BALENA_UUID],
        "onboarding_address": diagnostics[DIAG_JSON_KEYS.ONBOARDING_KEY],
        "public_address": diagnostics[DIAG_JSON_KEYS.PUBLIC_KEY],
        "serial_number": diagnostics[DIAG_JSON_KEYS.SERIAL_NUMBER],
        "variant": diagnostics[DIAG_JSON_KEYS.VARIANT]
    }
    return device_payload


def register_third_party_miner() -> None:
    '''
    tries to register a non nebra miner with dashboard
    '''
    try:
        diagnostics = cached_diagnostics_data()
        if is_nebra_device(diagnostics):
            log.info("nebra devices are registered in manufacturing")
            return

        # commenting for now, it is creating issues for us. Now that some devices have been
        # erroneously marked registered, we can't really keep it at the moment. if we decide
        # to enable this later, we should also take care of all the sub errors that might
        # happen for HTTP 400. Right now trying to re-register also returns 400.
        # if is_registered():
        #     log.info("local db state: miner already registered with dashboard.")
        #     return

        payload = _prepare_registration_payload(diagnostics)
        register = requests.post(THIRD_PARTY_MINER_REGISTRATION_URL, data=json.dumps(payload),
                                 headers={'Content-Type': 'application/json; charset=UTF-8'})

        if register.status_code < 300:
            log.info("dashboard: miner successfully registered.")
            set_registered(True)
        else:
            log.error(f"dashboard: failed registration: {register} {register.text}")
    except KeyError as e:
        log.error(f"failed registration, missing key in diagnostics {e}")
    except Exception as e:
        log.error(f"failed registration, unknown error {e}")


def claim_miner_deeplink() -> str:
    '''
    returns encoded deeplink for claiming the device in dashboard.
    '''
    diagnostics = cached_diagnostics_data()

    query_params = {
        'serial_number': diagnostics.get(DIAG_JSON_KEYS.SERIAL_NUMBER, "00000000000"),
        'eth_mac': diagnostics.get(DIAG_JSON_KEYS.ETH_MAC_ADDRESS, "00:00:00:00:00:00")
    }

    # named tuple matching urlparse/unparse argument tuple.
    Components = namedtuple(
        typename='Components',
        field_names=['scheme', 'netloc', 'url', 'path', 'query', 'fragment']
    )

    # parse the url and unparse after adding query parameters
    components = Components(*urlparse(MINER_CLAIM_URL))
    components = components._replace(query=urlencode(query_params))
    url = urlunparse(components)

    return url
