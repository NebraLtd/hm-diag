import unittest
from unittest.mock import patch
import os
import responses
import tempfile

from hw_diag.utilities.download import validate_file, download_with_resume

TESTDATA_FILENAME = os.path.join(os.path.dirname(__file__), "data/nebra.webp")
TESTDATA_SHA256 = "aa3fbe2ddc4ea2ced20ce5d5a34b0f4b618a22bc0656d48a8be2166202d3a00c"

TEST_BLOCK_SIZE = 1024

OUTPUT_FILENAME = "nebra.webp"

MOCK_DOWNLOAD_URL = "https://example.com/test.webp"
MOCK_DOWNLOAD_CONTENT_TYPE = "image/webp"


def get_test_data():
    """
    Return the test data for download_with_resume
    """
    with open(TESTDATA_FILENAME, "rb") as f:
        data = f.read()
        return data


def add_head_response(data):
    responses.add(
        responses.HEAD,
        MOCK_DOWNLOAD_URL,
        status=200,
        content_type=MOCK_DOWNLOAD_CONTENT_TYPE,
        headers={"Content-Length": f"{len(data)}"},
    )


def add_file_chunk_response(data, start, end):
    data_len = len(data)
    responses.add(
        responses.GET,
        MOCK_DOWNLOAD_URL,
        body=data[start:end],
        status=200,
        content_type=MOCK_DOWNLOAD_CONTENT_TYPE,
        headers={
            "Content-Length": f"{data_len}",
            "Content-Range": f"bytes {start}-{end}/{data_len}",
        },
    )


def add_not_found_response():
    responses.add(
        responses.GET,
        MOCK_DOWNLOAD_URL,
        status=404,
        content_type=MOCK_DOWNLOAD_CONTENT_TYPE,
    )


class TestDownload(unittest.TestCase):

    # @patch(requests.get, read_stream)
    @patch("hw_diag.utilities.download.DEFAULT_BLOCK_SIZE", 1024)
    @responses.activate
    def test_download(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_data = get_test_data()
            data_len = len(test_data)
            tmpfilename = os.path.join(tmpdir, OUTPUT_FILENAME)

            # add responses in the order they will be required.
            # header
            add_head_response(test_data)

            # partial file
            add_file_chunk_response(test_data, 0, 1024)

            # this will download part file as only 1024 bytes will be served.
            download_with_resume(MOCK_DOWNLOAD_URL, tmpfilename, TESTDATA_SHA256)
            part_filename = f"{tmpfilename}.part"
            self.assertEqual(os.path.exists(part_filename), True)
            self.assertEqual(validate_file(part_filename, TESTDATA_SHA256), False)

            # prepare for next test that completes the download
            add_head_response(test_data)
            add_file_chunk_response(test_data, 1024, data_len)

            # this will complete the file
            download_with_resume(MOCK_DOWNLOAD_URL, tmpfilename, TESTDATA_SHA256)
            self.assertEqual(os.path.exists(part_filename), False)
            self.assertEqual(os.path.exists(tmpfilename), True)
            self.assertEqual(validate_file(tmpfilename, hash=TESTDATA_SHA256), True)

    @patch("hw_diag.utilities.download.DEFAULT_BLOCK_SIZE", 1024)
    @responses.activate
    def test_file_not_found(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_data = get_test_data()
            tmpfilename = os.path.join(tmpdir, OUTPUT_FILENAME)

            # test for file not found
            add_head_response(test_data)
            add_not_found_response()

            self.assertEqual(os.path.exists(tmpfilename), False)
            download_with_resume(MOCK_DOWNLOAD_URL, tmpfilename, TESTDATA_SHA256)
            self.assertEqual(os.path.exists(tmpfilename), False)

    def test_validate_file(self):
        block_variable_name = "hw_diag.utilities.download.DEFAULT_BLOCK_SIZE"
        with patch(block_variable_name, 1024) as _:
            self.assertTrue(validate_file(file_path=TESTDATA_FILENAME, hash=TESTDATA_SHA256))
        with patch(block_variable_name, 32) as _:
            self.assertTrue(validate_file(file_path=TESTDATA_FILENAME, hash=TESTDATA_SHA256))
