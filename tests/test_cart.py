import unittest
from decimal import Decimal

from shopkit.cart import Cart


class CartTests(unittest.TestCase):
    def test_subtotal_sums_lines(self):
        cart = Cart()
        cart.add("apple", Decimal("1.25"), 4)
        cart.add("pear", Decimal("2.00"))
        self.assertEqual(cart.subtotal(), Decimal("7.00"))

    def test_unique_skus(self):
        cart = Cart()
        cart.add("apple", Decimal("1.25"))
        cart.add("pear", Decimal("2.00"))
        cart.add("apple", Decimal("1.25"))
        self.assertEqual(cart.unique_skus(), ["apple", "pear"])

    def test_empty_cart_is_zero(self):
        self.assertEqual(Cart().subtotal(), Decimal("0"))

    def test_rejects_zero_quantity(self):
        with self.assertRaises(ValueError):
            Cart().add("apple", Decimal("1.25"), 0)
