import os
import requests
from requests.exceptions import ConnectionError, ConnectTimeout

from hm_pyhelper.logger import get_logger

log = get_logger(__name__)


class BalenaSupervisor:

    def __init__(self, supervisor_address: str, supervisor_api_key: str):
        self.supervisor_address = supervisor_address
        self.supervisor_api_key = supervisor_api_key
        self.headers = {'Content-type': 'application/json'}

    @classmethod
    def new_from_env(cls):
        return cls(
            os.environ['BALENA_SUPERVISOR_ADDRESS'], os.environ['BALENA_SUPERVISOR_API_KEY'])

    def _make_request(self, http_method, endpoint):
        url = f"{self.supervisor_address}{endpoint}?apikey={self.supervisor_api_key}"

        try:
            return requests.request(method=http_method, url=url, headers=self.headers)

        except (ConnectionError, ConnectTimeout) as requests_exception:
            log.error(f"Connection error while trying to shutdown device. URL: {url}")

            log.error(requests_exception)

        except Exception as exp:
            log.error(f"Error while trying to shutdown device. URL: {url}")
            log.error(exp)

        return None

    def shutdown(self):
        "Attempt device shutdown using balena supervisor API."
        log.info("Attempting device shutdown using Balena supervisor.")

        response = self._make_request('POST', '/v1/shutdown')
        if response is None or response.ok is False:
            log.error("Device shutdown attempt failed.")

        return response.json()

    def get_device_status(self) -> str:
        "Get device status from balena supervisor API."
        log.info("Attempting device shutdown using Balena supervisor.")

        response = self._make_request('GET', '/v2/state/status')
        if response is None or response.ok is False:
            log.error("Device status request failed.")
            return ''

        return response.json().get('status', 'unknown')
