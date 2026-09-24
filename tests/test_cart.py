import unittest
from decimal import Decimal

from shopkit.cart import Cart, Line


class CartTests(unittest.TestCase):
    def test_subtotal_sums_lines(self):
        cart = Cart()
        cart.add(Line("apple", Decimal("1.25"), 4))
        cart.add(Line("pear", Decimal("2.00")))
        self.assertEqual(cart.subtotal(), Decimal("7.00"))

    def test_empty_cart_is_zero(self):
        self.assertEqual(Cart().subtotal(), Decimal("0"))

    def test_rejects_zero_quantity(self):
        with self.assertRaises(ValueError):
            Cart().add(Line("apple", Decimal("1.25"), 0))
