import unittest
from unittest.mock import patch
import sys
import os
sys.path.append("..")
from utils import get_env_var # noqa


class TestGetEnvVariable(unittest.TestCase):

    @patch('os.getenv')
    def test_get_var(self, null):
        os.getenv.return_value = "1"
        result = get_env_var("VAR")
        self.assertEqual(result, '1')

    def test_get_null_var(self):
        result = get_env_var("VAR")
        self.assertEqual(result, None)
