import unittest
from unittest.mock import patch, Mock
import sys
sys.path.append("..")
from utils import config_search_param # noqa


class TestConfigSearch(unittest.TestCase):
    @patch('subprocess.Popen')
    def test_correct_param(self, mock_subproc_popen):
        process_mock = Mock()
        attrs = {'communicate.return_value': (str.encode("60--"), 'error')}
        process_mock.configure_mock(**attrs)
        mock_subproc_popen.return_value = process_mock
        result = config_search_param("somecommand", "60--")
        self.assertEqual(result, True)

    @patch('subprocess.Popen')
    def test_incorrect_param(self, mock_subproc_popen):
        process_mock = Mock()
        attrs = {'communicate.return_value': (str.encode('output'), 'error')}
        process_mock.configure_mock(**attrs)
        mock_subproc_popen.return_value = process_mock
        result = config_search_param("somecommand", "60--")
        self.assertEqual(result, False)

    def test_types(self):
        self.assertRaises(TypeError, config_search_param, 1, 2)
        self.assertRaises(TypeError, config_search_param, "123321", 1)
        self.assertRaises(TypeError, config_search_param, 1, "123321")
