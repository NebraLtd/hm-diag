import unittest
from unittest.mock import patch
import responses
import os

from hw_diag.utilities.system_metrics import get_balena_metrics
from hw_diag.tests.test_balena_supervisor import valid_status_json, \
    TEST_SUPERVISOR_ADDRESS, TEST_SUPERVISOR_API_KEY, TEST_SUPERVISOR_DEVICE_STATUS_URL


class TestSystemMetrics(unittest.TestCase):

    @patch.dict(
        os.environ,
        {
            'BALENA_SUPERVISOR_ADDRESS': TEST_SUPERVISOR_ADDRESS,
            'BALENA_SUPERVISOR_API_KEY': TEST_SUPERVISOR_API_KEY
        },
        clear=True
    )
    @responses.activate
    def test_balena_metrics(self):
        responses.add(
            responses.GET,
            TEST_SUPERVISOR_DEVICE_STATUS_URL,
            status=200,
            json=valid_status_json()
        )

        metrics = get_balena_metrics()
        self.assertEqual(metrics["balena_release"], valid_status_json()["release"])

    @patch.dict(
        os.environ,
        {
            'BALENA_SUPERVISOR_ADDRESS': TEST_SUPERVISOR_ADDRESS,
            'BALENA_SUPERVISOR_API_KEY': TEST_SUPERVISOR_API_KEY
        },
        clear=True
    )
    @responses.activate
    def test_balena_metrics_fail(self):
        responses.add(
            responses.GET,
            TEST_SUPERVISOR_DEVICE_STATUS_URL,
            status=200,
            json={"status": "error"}
        )
        metrics = get_balena_metrics()
        self.assertEqual(metrics, {"balena_api_status": "error", "balena_failed_containers": []})
