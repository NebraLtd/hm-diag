import unittest

from bigquery.bigquery_to_pydantic import get_pydantic_type


class TestBigquery(unittest.TestCase):
    def test_get_pydantic_type_required(self):
        result = get_pydantic_type("STRING", "REQUIRED")
        self.assertEqual(result, "str")

    def test_get_pydantic_type_repeated(self):
        result = get_pydantic_type("INTEGER", "REPEATED")
        self.assertEqual(result, "List[int]")
