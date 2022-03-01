import unittest
from unittest.mock import patch
import os
import responses

from hw_diag.utilities.download import validate_file, download_with_resume

TESTDATA_FILENAME = os.path.join(os.path.dirname(__file__), 'data/nebra.webp')
TESTDATA_SHA256 = 'aa3fbe2ddc4ea2ced20ce5d5a34b0f4b618a22bc0656d48a8be2166202d3a00c'

TEST_BLOCK_SIZE = 1024

OUTPUT_FILENAME = '/tmp/nebra.webp'


def get_test_data():
    """
    Return the test data for download_with_resume
    """
    with open(TESTDATA_FILENAME, 'rb') as f:
        data = f.read()
        return data


def add_head_response(data):
    responses.add(responses.HEAD, 'http://example.com/test.webp',
                  status=200,
                  content_type='image/webp',
                  headers={'Content-Length': f'{len(data)}'})


def add_file_chunk_response(data, start, end):
    data_len = len(data)
    responses.add(responses.GET, 'http://example.com/test.webp',
                  body=data[start:end],
                  status=200,
                  content_type='image/webp',
                  headers={'Content-Length': f'{data_len}',
                               'Content-Range': f'bytes {start}-{end}/{data_len}'})


def add_not_found_response():
    responses.add(responses.GET, 'http://example.com/test.webp',
                  status=404,
                  content_type='image/webp')


class TestDownload(unittest.TestCase):

    def setUp(self) -> None:
        self.cleanup()
        return super().setUp()

    def cleanup(self) -> None:
        for filename in [OUTPUT_FILENAME, OUTPUT_FILENAME + '.part']:
            if os.path.exists(filename):
                os.remove(filename)

        responses.reset()

    # @patch(requests.get, read_stream)
    @patch('hw_diag.utilities.download.DEFAULT_BLOCK_SIZE', 1024)
    @responses.activate
    def test_download(self):
        test_data = get_test_data()
        data_len = len(test_data)

        # add responses in the order they will be required.
        # header
        add_head_response(test_data)

        # partial file
        add_file_chunk_response(test_data, 0, 1024)

        # this will download part file as only 1024 bytes will be served.
        download_with_resume('http://example.com/test.webp',
                             OUTPUT_FILENAME, TESTDATA_SHA256)
        part_filename = f'{OUTPUT_FILENAME}.part'
        self.assertEqual(os.path.exists(part_filename), True)
        self.assertEqual(validate_file(part_filename, TESTDATA_SHA256), False)

        # prepare for next test
        add_head_response(test_data)
        add_file_chunk_response(test_data, 1024, data_len)

        # this will complete the file
        download_with_resume('http://example.com/test.webp',
                             OUTPUT_FILENAME, TESTDATA_SHA256)
        self.assertEqual(os.path.exists(part_filename), False)
        self.assertEqual(os.path.exists(OUTPUT_FILENAME), True)
        self.assertEqual(validate_file(OUTPUT_FILENAME, hash=TESTDATA_SHA256), True)

        # cleanup
        self.cleanup()
        add_head_response(test_data)
        add_not_found_response()

        self.assertEqual(os.path.exists(part_filename), False)
        self.assertEqual(os.path.exists(OUTPUT_FILENAME), False)
        download_with_resume('http://example.com/test.webp',
                             OUTPUT_FILENAME, TESTDATA_SHA256)
        self.assertEqual(os.path.exists(OUTPUT_FILENAME), False)

    def test_validate_file(self):
        block_variable_name = 'hw_diag.utilities.download.DEFAULT_BLOCK_SIZE'
        with patch(block_variable_name, 1024) as _:
            self.assertTrue(validate_file(file_path=TESTDATA_FILENAME, hash=TESTDATA_SHA256))
        with patch(block_variable_name, 32) as _:
            self.assertTrue(validate_file(file_path=TESTDATA_FILENAME, hash=TESTDATA_SHA256))
