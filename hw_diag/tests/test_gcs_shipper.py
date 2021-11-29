import unittest

from unittest.mock import patch
from unittest.mock import MagicMock

from hw_diag.utilities.gcs_shipper import convert_diagnostics_to_gcs_payload,\
                                          generate_hash
from hw_diag.utilities.gcs_shipper import upload_diagnostics


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
        diagnostics = {'PK': 'my_key'}
        retval = upload_diagnostics(diagnostics, True)
        self.assertTrue(retval)

    @patch('hw_diag.utilities.gcs_shipper.requests')
    def test_upload_diagnostics_invalid(self, mock_requests):
        mock_requests.post = MagicMock()
        mock_requests.post.return_value = ErrorResponse()
        diagnostics = {'PK': 'my_key'}
        retval = upload_diagnostics(diagnostics, True)
        self.assertFalse(retval)

    def test_upload_diagnostics_should_not_ship(self):
        diagnostics = {'PK': 'my_key'}
        retval = upload_diagnostics(diagnostics, False)
        self.assertIsNone(retval)

    def test_diagnostics_to_gcs_payload(self):
        diagnostics = {
            "serial_number": "00000000baa3ac7c",
        }
        diagnostics = convert_diagnostics_to_gcs_payload(diagnostics)
        self.assertTrue('RPI' in diagnostics and
                        'last_updated_ts' in diagnostics and
                        'uptime_days' in diagnostics and
                        'serial_number' not in diagnostics)
