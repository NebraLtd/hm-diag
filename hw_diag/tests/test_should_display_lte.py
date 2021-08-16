import unittest
from hw_diag.utilities.hardware import should_display_lte


class TestShouldDisplayLTE(unittest.TestCase):

    def test_known_lte_variant(self):
        variant = 'NEBHNT-OUT1'
        diagnostics = {'VA': variant}
        result = should_display_lte(diagnostics)
        self.assertTrue(result)

    def test_known_non_lte_variant(self):
        variant = 'NEBHNT-IN1'
        diagnostics = {'VA': variant}
        result = should_display_lte(diagnostics)
        self.assertFalse(result)
