import os

import requests
from requests.exceptions import ConnectionError, ConnectTimeout

from hm_pyhelper.logger import get_logger

LOGGER = get_logger(__name__)


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
            LOGGER.error(f"Connection error while trying to shutdown device. URL: {url}")

            LOGGER.error(requests_exception)

        except Exception as exp:
            LOGGER.error(f"Error while trying to shutdown device. URL: {url}")
            LOGGER.error(exp)

        return None

    def shutdown(self):
        """Attempt device shutdown using balena supervisor API."""
        LOGGER.info("Attempting device shutdown using Balena supervisor.")

        response = self._make_request('POST', '/v1/shutdown')
        if response is None or response.ok is False:
            LOGGER.error("Device shutdown attempt failed.")
            raise Exception('supervisor API not accessible')

        try:
            return response.json()
        except Exception:
            raise Exception('shutdown failed due to supervisor API issue')

    def get_device_status(self, key_to_return) -> str:
        """Get device status from balena supervisor API."""
        LOGGER.info("Retrieving device status using Balena supervisor.")

        response = self._make_request('GET', '/v2/state/status')
        if response is None or response.ok is False:
            LOGGER.error("Device status request failed.")
            raise Exception("Device status request failed")

        try:
            return response.json()[key_to_return]
        except Exception:
            return 'Failed due to supervisor API issue'
