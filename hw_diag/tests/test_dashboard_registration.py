import unittest
from unittest.mock import patch
import responses

from hw_diag.app import get_app
from hw_diag.utilities.dashboard_registration import register_third_party_miner, \
    claim_miner_deeplink, THIRD_PARTY_MINER_REGISTRATION_URL
from hw_diag.tests.fixtures.diagnostic_results import SAMPLE_DIAGNOSTICS
from hw_diag.constants import DIAG_JSON_KEYS

# from hw_diag.utilities.db.get_value


def non_nebra_daig_data():
    sample_data = SAMPLE_DIAGNOSTICS.copy()
    sample_data[DIAG_JSON_KEYS.FRIENDLY_NAME] = "syncrobit fl1"
    return sample_data


def add_registration_success_response():
    responses.add(
        responses.POST,
        url=THIRD_PARTY_MINER_REGISTRATION_URL,
        status=201
    )


def add_registration_exists_response():
    # miner already exits
    responses.add(
        responses.POST,
        url=THIRD_PARTY_MINER_REGISTRATION_URL,
        status=400
    )


def add_registration_failure_response():
    # miner already exits
    responses.add(
        responses.POST,
        url=THIRD_PARTY_MINER_REGISTRATION_URL,
        status=404
    )


class TestDashboardRegistration(unittest.TestCase):
    def setUp(self):
        self.app = get_app('test_app', lean_initializations=False)
        # self.client = self.app.test_client()

    @responses.activate
    @patch('hw_diag.utilities.dashboard_registration.cached_diagnostics_data',
           return_value=non_nebra_daig_data())
    @patch('hw_diag.utilities.dashboard_registration.get_value', return_value=None)
    @patch('hw_diag.utilities.dashboard_registration.set_value')
    def test_miner_registration_success(self, set_value_mock,
                                        get_value_mock, _):
        add_registration_success_response()
        with self.app.app_context():
            register_third_party_miner()
            # test set_value was called with is_registered to true
            self.assertEqual(set_value_mock.call_count, 1)
            args, _ = set_value_mock.call_args
            self.assertEqual(args[1], str(True))

    @responses.activate
    @patch('hw_diag.utilities.dashboard_registration.cached_diagnostics_data',
           return_value=non_nebra_daig_data())
    @patch('hw_diag.utilities.dashboard_registration.get_value', return_value=None)
    @patch('hw_diag.utilities.dashboard_registration.set_value')
    def test_miner_registration_exits(self, set_value_mock,
                                      get_value_mock, _):
        add_registration_exists_response()
        with self.app.app_context():
            register_third_party_miner()
            # test set_value was called with is_registered to true
            self.assertEqual(set_value_mock.call_count, 0)

    @responses.activate
    @patch('hw_diag.utilities.dashboard_registration.cached_diagnostics_data',
           return_value=non_nebra_daig_data())
    @patch('hw_diag.utilities.dashboard_registration.get_value', return_value=None)
    @patch('hw_diag.utilities.dashboard_registration.set_value')
    def test_miner_registration_failure(self, set_value_mock,
                                        get_value_mock, _):
        add_registration_failure_response()
        with self.app.app_context():
            register_third_party_miner()
            # test set_value was called with is_registered to true
            self.assertEqual(set_value_mock.call_count, 0)

    @patch('hw_diag.utilities.dashboard_registration.cached_diagnostics_data',
           return_value=SAMPLE_DIAGNOSTICS)
    @patch('hw_diag.utilities.dashboard_registration.get_value', return_value=None)
    @patch('hw_diag.utilities.dashboard_registration.set_value')
    def test_nebra_miner_registration(self, set_value_mock,
                                      get_value_mock, _):
        with self.app.app_context():
            register_third_party_miner()
            # test set_value was called with is_registered to true
            self.assertEqual(set_value_mock.call_count, 0)
            self.assertEqual(get_value_mock.call_count, 0)

    @patch('hw_diag.utilities.dashboard_registration.cached_diagnostics_data',
           return_value=SAMPLE_DIAGNOSTICS)
    def test_claim_miner_deeplink(self, _):
        url = claim_miner_deeplink()
        expected_url = "https://dashboard.nebra.com/devices/" + \
            "?serial_number=000000009e3cb787&eth_mac=00%3ABD%3A27%3A78%3A2E%3A5D#qr-modal"
        self.assertEqual(url, expected_url)
