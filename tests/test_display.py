import unittest
from decimal import Decimal

from shopkit.display import money


class MoneyTests(unittest.TestCase):
    def test_thousands_separator(self):
        self.assertEqual(money(Decimal("1234.5")), "$1,234.50")

    def test_small_amount(self):
        self.assertEqual(money(Decimal("9.99")), "$9.99")
