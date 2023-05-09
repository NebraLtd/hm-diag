import os
from typing import Optional

import requests
from requests.exceptions import ConnectionError, ConnectTimeout

from hm_pyhelper.logger import get_logger

LOGGER = get_logger(__name__)


class BalenaCloud:

    def __init__(self, api_url: str, api_key: str, app_id: str, device_uuid: str):
        self.api_url: str = api_url
        self.app_id: str = app_id
        self.device_uuid: str = device_uuid
        self.headers = {'Content-type': 'application/json', 'Authorization': f'Bearer {api_key}'}

        self._device_id: Optional[int] = None

    @classmethod
    def new_from_env(cls):
        return cls(
            os.environ['BALENA_API_URL'],
            os.environ['BALENA_API_KEY'],
            os.environ['BALENA_APP_ID'],
            os.environ['BALENA_DEVICE_UUID'],
        )

    def _make_request(self, http_method, endpoint, **kwargs):
        url = f'{self.api_url}{endpoint}'

        try:
            resp = requests.request(method=http_method, url=url, headers=self.headers, **kwargs)
            LOGGER.info(resp.status_code)
            LOGGER.info(resp.text)
            return resp

        except (ConnectionError, ConnectTimeout) as requests_exception:
            LOGGER.error(f'API connection error. URL: {url}')
            LOGGER.error(requests_exception)

        except Exception as exp:
            LOGGER.error(f'API error. URL: {url}')
            LOGGER.error(exp)

        return None

    def _get_device_id(self) -> int:
        response = self._make_request(
            'GET',
            f'/v6/device?$filter=uuid%20eq%20\'{self.device_uuid}\''
        )
        if response is None or response.ok is False:
            raise RuntimeError('Device ID unavailable: API error')

        try:
            data = response.json()
            data = data['d']
        except Exception:
            raise RuntimeError('Device ID unavailable: unexpected API response')

        try:
            return data[0]['id']
        except (KeyError, IndexError):
            raise RuntimeError('Device ID unavailable: device not registered on cloud')

    def get_device_id(self) -> int:
        if self._device_id is None:
            self._device_id = self._get_device_id()
            LOGGER.info(f'Got device ID {self._device_id}.')

        return self._device_id

    def get_fleet_config_variables(self) -> list[dict]:
        """Get fleet config variables associated to this device's fleet, from the cloud.
        Returns a list containing a dict with details of each config variable."""

        LOGGER.info("Retrieving fleet config variables from cloud.")

        response = self._make_request(
            'GET',
            f'/v6/application_config_variable?$filter=application%20eq%20{self.app_id}',
        )

        if response is None or response.ok is False:
            raise RuntimeError('Failed to retrieve fleet config variables: API error')

        try:
            data = response.json()
            return data['d']
        except Exception:
            raise RuntimeError('Failed to retrieve fleet config variables: unexpected API response')

    def get_device_config_variables(self) -> list[dict]:
        """Get device config variables associated to this device, from the cloud.
        Returns a list containing a dict with details of each config variable."""

        LOGGER.info('Retrieving device config variables from cloud.')

        response = self._make_request(
            'GET',
            f'/v6/device_config_variable?$filter=device%20eq%20{self.get_device_id()}',
        )

        if response is None or response.ok is False:
            raise RuntimeError('Failed to retrieve device config variables: API error')

        try:
            data = response.json()
            return data['d']
        except Exception:
            raise RuntimeError(
                'Failed to retrieve device config variables: unexpected API response'
            )

    def create_device_config_variable(self, name: str, value: str) -> dict:
        """Create a device config variable associated to this device, on the cloud.
        Returns a dict with details of the newly created config variable."""

        LOGGER.info(f'Creating variable {name}="{value}".')

        response = self._make_request(
            'POST',
            '/v6/device_config_variable',
            json={
                'device': self.get_device_id(),
                'name': name,
                'value': value,
            }
        )

        if response is None or response.ok is False:
            raise RuntimeError('Failed to create device config variable: API error')

        try:
            return response.json()
        except Exception:
            raise RuntimeError('Failed to create device config variable: unexpected API response')

    def update_device_config_variable(self, variable_id: int, value: str) -> None:
        """Update a device config variable associated to this device, on the cloud."""

        LOGGER.info(f'Updating variable with id {variable_id} to "{value}".')

        response = self._make_request(
            'PATCH',
            f'/v6/device_config_variable({variable_id})',
            json={'value': value}
        )

        if response is None or response.ok is False:
            raise RuntimeError('Failed to update device config variable: API error')

    def remove_device_config_variable(self, variable_id: int) -> None:
        """Remove a device config variable associated to this device, from the cloud.
        Note: this doesn't really work due to some permission errors (status code 401)."""

        LOGGER.info(f'Removing variable with id {variable_id}.')

        response = self._make_request(
            'DELETE',
            f'/v6/device_config_variable({variable_id})',
        )

        if response is None or response.ok is False:
            raise RuntimeError('Failed to remove device config variable: API error')
