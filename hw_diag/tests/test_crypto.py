import hashlib
import unittest
from unittest.mock import mock_open, patch
from hw_diag.utilities.crypto import calculate_file_hash, empty_hash


def mock_file_read(chunk_size):
    return b'This is a sample chunk.'


class CalculateFileHashTestCase(unittest.TestCase):
    def test_calculate_file_hash_single_file(self):
        file_path = 'file1.txt'
        expected_hash = hashlib.sha256(b'This is a sample chunk.').hexdigest()

        with patch('builtins.open', mock_open(read_data=b'This is a sample chunk.')):
            result = calculate_file_hash([file_path])

        self.assertEqual(result, expected_hash)

    def test_calculate_file_hash_multiple_files(self):
        file_paths = ['file1.txt', 'file2.txt', 'file3.txt']
        expected_hash = hashlib.sha256(b'This is a sample chunk.' * 3).hexdigest()

        with patch('builtins.open', mock_open(read_data=b'This is a sample chunk.')):
            result = calculate_file_hash(file_paths)

        self.assertEqual(result, expected_hash)

    def test_calculate_file_hash_no_files(self):
        file_paths = []
        expected_hash = hashlib.sha256(b'').hexdigest()

        result = calculate_file_hash(file_paths)

        self.assertEqual(result, expected_hash)

    def test_empty_hash(self):
        expected_hash = hashlib.sha256(b'').hexdigest()

        result = empty_hash()

        self.assertEqual(result, expected_hash)


if __name__ == '__main__':
    unittest.main()
