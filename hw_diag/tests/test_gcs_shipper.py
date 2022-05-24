import unittest

from unittest.mock import patch
from unittest.mock import MagicMock

from functools import lru_cache
import json
from os.path import abspath, dirname, join

from hw_diag.utilities.gcs_shipper import add_timestamp_to_diagnostics,\
                                          generate_hash
from hw_diag.utilities.gcs_shipper import upload_diagnostics


@lru_cache(maxsize=None)
def valid_diagnostic_data():
    json_full_path = join(dirname(abspath(__file__)), 'data/valid_diagnostics.json')
    return json.load(open(json_full_path, 'r'))


class OKResponse(object):
    status_code = 200


class ErrorResponse(object):
    status_code = 500
    text = 'Internal Server Error'


class TestGenerateHash(unittest.TestCase):

    def test_generate_hash(self):
        result = generate_hash('public_key')
        self.assertEqual(len(result), 64)


class TestUploadDiagnostics(unittest.TestCase):

    @patch('hw_diag.utilities.gcs_shipper.requests')
    def test_upload_diagnostics_valid(self, mock_requests):
        mock_requests.post = MagicMock()
        mock_requests.post.return_value = OKResponse()
        retval = upload_diagnostics(valid_diagnostic_data(), True)
        self.assertTrue(retval)

    @patch('hw_diag.utilities.gcs_shipper.requests')
    def test_diagnostics_missing_required_field(self, mock_requests):
        mock_requests.post = MagicMock()
        mock_requests.post.return_value = OKResponse()
        diag_data = valid_diagnostic_data().copy()
        diag_data.pop('serial_number')
        retval = upload_diagnostics(diag_data, True)
        self.assertFalse(retval)

    @patch('hw_diag.utilities.gcs_shipper.requests')
    def test_diagnostics_missing_optional_field(self, mock_requests):
        mock_requests.post = MagicMock()
        mock_requests.post.return_value = OKResponse()
        diag_data = valid_diagnostic_data().copy()
        diag_data.pop('ECC')
        retval = upload_diagnostics(diag_data, True)
        self.assertTrue(retval)

    @patch('hw_diag.utilities.gcs_shipper.requests')
    def test_upload_diagnostics_failed_upload(self, mock_requests):
        mock_requests.post = MagicMock()
        mock_requests.post.return_value = ErrorResponse()
        retval = upload_diagnostics(valid_diagnostic_data(), True)
        self.assertFalse(retval)

    def test_upload_diagnostics_should_not_ship(self):
        retval = upload_diagnostics(valid_diagnostic_data(), False)
        self.assertIsNone(retval)

    def test_add_timestamp_to_diagnostics(self):
        diagnostics = {
            "serial_number": "00000000baa3ac7c",
        }
        diagnostics = add_timestamp_to_diagnostics(diagnostics)
        self.assertTrue(
            'last_updated_ts' in diagnostics and
            'serial_number' in diagnostics)
