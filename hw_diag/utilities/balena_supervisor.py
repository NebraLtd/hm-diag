import os

import requests
from requests.exceptions import ConnectionError, ConnectTimeout

from hm_pyhelper.logger import get_logger

LOGGER = get_logger(__name__)
SUPERVISOR_CONNECTIVITY_ERROR = 'supervisor API not accessible'


class BalenaSupervisor:

    def __init__(self, supervisor_address: str, supervisor_api_key: str, app_id: str):
        self.supervisor_address = supervisor_address
        self.supervisor_api_key = supervisor_api_key
        self.app_id = app_id
        self.headers = {'Content-type': 'application/json'}

    @classmethod
    def new_from_env(cls):
        return cls(
            os.environ['BALENA_SUPERVISOR_ADDRESS'],
            os.environ['BALENA_SUPERVISOR_API_KEY'],
            os.environ['BALENA_APP_ID']
        )

    def _make_request(self, http_method, endpoint, **kwargs):
        url = f"{self.supervisor_address}{endpoint}?apikey={self.supervisor_api_key}"

        try:
            resp = requests.request(method=http_method, url=url, headers=self.headers, **kwargs)
            LOGGER.info(resp.status_code)
            LOGGER.info(resp.text)
            return resp

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
            raise RuntimeError(SUPERVISOR_CONNECTIVITY_ERROR)

        try:
            return response.json()
        except Exception:
            raise RuntimeError('shutdown failed due to supervisor API issue')

    def restart(self):
        """Attempt to restart containers using balena supervisor API."""
        LOGGER.info("Attempting container restart using Balena supervisor.")

        payload = {
            'appId': self.app_id
        }

        response = self._make_request('POST', '/v1/restart', json=payload)
        if response is None or response.ok is False:
            LOGGER.error("Container restart attempt failed.")
            raise RuntimeError(SUPERVISOR_CONNECTIVITY_ERROR)

        try:
            return response.json()
        except Exception:
            raise RuntimeError('Restart failed due to supervisor API issue')

    def purge(self):
        """Attempt to purge data using balena supervisor API."""
        LOGGER.info("Attempting data purge using Balena supervisor.")

        payload = {
            'appId': self.app_id
        }

        response = self._make_request('POST', '/v1/purge', json=payload)
        if response is None or response.ok is False:
            LOGGER.error("Purge attempt failed.")
            raise RuntimeError(SUPERVISOR_CONNECTIVITY_ERROR)

        try:
            return response.json()
        except Exception:
            raise RuntimeError('Purge failed due to supervisor API issue')

    def reboot(self, force: bool = False):
        """Attempt device reboot using balena supervisor API."""
        LOGGER.info("Attempting device reboot using Balena supervisor.")

        """Reboots the device. This will first try to stop running services, and fail if
        there is an update lock. An optional "force" parameter in the body overrides the lock
        when true (and the lock can also be overridden from the dashboard)."""
        if force:
            response = self._make_request('POST', '/v1/reboot', json={'force': True})
        else:
            response = self._make_request('POST', '/v1/reboot')

        if response is None or response.ok is False:
            LOGGER.error("Device restart attempt failed.")
            raise RuntimeError(SUPERVISOR_CONNECTIVITY_ERROR)

        try:
            return response.json()
        except Exception:
            raise RuntimeError('reboot failed due to supervisor API issue')

    def get_device_status(self, key_to_return=None) -> str:
        """Get device status from balena supervisor API.
        Returns value of the supplied key_to_return other full response json object."""
        LOGGER.info("Retrieving device status using Balena supervisor.")

        response = self._make_request('GET', '/v2/state/status')

        error_msg = ""
        if response is None:
            error_msg = "Device status request failed. No response received."

        elif response.ok is False:
            error_msg = "Device status request failed. Got non-OK response: " + \
                f"{response.status_code} {response.content}"

        if error_msg:
            LOGGER.warning(error_msg)
            raise RuntimeError(error_msg)

        try:
            if key_to_return:
                return response.json()[key_to_return]
            return response.json()
        except ValueError:
            error_msg = "Supervisor API did not return valid json response.\n" + \
                        f"Response content: {response.content}"
            LOGGER.warning(error_msg)
            raise RuntimeError(error_msg)
        except Exception:
            error_msg = f"Couldn't find {key_to_return} key in response.\n" + \
                        f"Response content: {response.content}"
            LOGGER.warning(error_msg)
            raise RuntimeError(error_msg)

    def get_device_config(self, key_to_return=None) -> str:
        LOGGER.info("Retrieving device config using Balena supervisor.")

        response = self._make_request('GET', '/v1/device/host-config')

        error_msg = ""
        if response is None:
            error_msg = "Device config request failed. No response received."

        elif response.ok is False:
            error_msg = "Device config request failed. Got non-OK response: " + \
                f"{response.status_code} {response.content}"

        if error_msg:
            LOGGER.warning(error_msg)
            raise RuntimeError(error_msg)

        try:
            if key_to_return:
                return response.json()[key_to_return]
            return response.json()
        except ValueError:
            error_msg = "Supervisor API did not return valid json response."
            LOGGER.warning(error_msg)
            raise RuntimeError(error_msg)
        except Exception:
            error_msg = f"Couldn't find {key_to_return} key in response.\n" + \
                        f"Response content: {response.content}"
            LOGGER.warning(error_msg)
            raise RuntimeError(error_msg)

    def get_device(self, key_to_return=None) -> str:
        LOGGER.info("Retrieving device data using Balena supervisor.")

        response = self._make_request('GET', '/v1/device')

        error_msg = ""
        if response is None:
            error_msg = "Device info request failed. No response received."

        elif response.ok is False:
            error_msg = "Device info request failed. Got non-OK response: " + \
                f"{response.status_code} {response.content}"

        if error_msg:
            LOGGER.warning(error_msg)
            raise RuntimeError(error_msg)

        try:
            if key_to_return:
                return response.json()[key_to_return]
            return response.json()
        except ValueError:
            error_msg = "Supervisor API did not return valid json response."
            LOGGER.warning(error_msg)
            raise RuntimeError(error_msg)
        except Exception:
            error_msg = f"Couldn't find {key_to_return} key in response.\n" + \
                        f"Response content: {response.content}"
            LOGGER.warning(error_msg)
            raise RuntimeError(error_msg)

    def set_hostname(self, hostname):
        LOGGER.info("Setting hostname via Balena supervisor.")
        url = '/v1/device/host-config'
        payload = {"network": {"hostname": hostname}}
        response = self._make_request('PATCH', url, json=payload)

        if response is None or response.ok is False:
            LOGGER.error("Set hostname attempt failed.")
            raise RuntimeError(SUPERVISOR_CONNECTIVITY_ERROR)

        return response
