import unittest
from decimal import Decimal

from shopkit.tax import rate_for


class RateForTests(unittest.TestCase):
    def test_known_state(self):
        self.assertEqual(rate_for("CA"), Decimal("7.25"))

    def test_untaxed_state(self):
        self.assertEqual(rate_for("OR"), Decimal("0"))

    def test_unknown_state_raises(self):
        with self.assertRaises(KeyError):
            rate_for("ZZ")
