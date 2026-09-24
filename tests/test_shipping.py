import unittest
from decimal import Decimal

from shopkit.shipping import shipping_cost


class ShippingTests(unittest.TestCase):
    def test_free_at_threshold(self):
        self.assertEqual(shipping_cost(Decimal("50.00")), Decimal("0.00"))

    def test_flat_rate_below_threshold(self):
        self.assertEqual(shipping_cost(Decimal("49.99")), Decimal("4.99"))
