import unittest
from unittest.mock import patch
import subprocess
import sys
sys.path.append("..")
from utils import config_search_param # noqa


class TestConfigSearch(unittest.TestCase):
    @patch('subprocess.Popen')
    def test_correct_param(self, null):
        subprocess.Popen.return_value = "60--"
        result = config_search_param("somecommand", "60--")
        self.assertEqual(result, True)

    @patch('subprocess.Popen')
    def test_incorrect_param(self, null):
        subprocess.Popen.return_value = "some param lister"
        result = config_search_param("somecommand", "60--")
        self.assertEqual(result, False)

    def test_types(self):
        self.assertRaises(TypeError, config_search_param, 1, 2)
        self.assertRaises(TypeError, config_search_param, "123321", 1)
        self.assertRaises(TypeError, config_search_param, 1, "123321")
