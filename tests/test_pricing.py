import unittest
from decimal import Decimal

from shopkit.pricing import add_tax, apply_discount


class ApplyDiscountTests(unittest.TestCase):
    def test_percentage_off(self):
        self.assertEqual(apply_discount(Decimal("19.99"), 15), Decimal("16.99"))

    def test_half_cent_rounds_up(self):
        self.assertEqual(apply_discount(Decimal("1.25"), 50), Decimal("0.63"))

    def test_zero_percent_is_unchanged(self):
        self.assertEqual(apply_discount(Decimal("8.40"), 0), Decimal("8.40"))

    def test_rejects_more_than_100_percent(self):
        with self.assertRaises(ValueError):
            apply_discount(Decimal("10.00"), 101)


class AddTaxTests(unittest.TestCase):
    def test_adds_tax(self):
        self.assertEqual(add_tax(Decimal("10.00"), Decimal("7.25")), Decimal("10.73"))

    def test_zero_rate_is_unchanged(self):
        self.assertEqual(add_tax(Decimal("10.00"), Decimal("0")), Decimal("10.00"))
