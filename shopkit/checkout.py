from collections.abc import Iterable
from decimal import Decimal

from shopkit.cart import Cart
from shopkit.pricing import add_tax, apply_discount
from shopkit.shipping import shipping_cost
from shopkit.tax import rate_for


def build_cart(items: Iterable[tuple[str, Decimal, int]]) -> Cart:
    cart = Cart()
    for sku, price, qty in items:
        cart.add(sku, price, qty)
    return cart


def order_total(cart: Cart, discount_percent: int = 0, state: str = "OR") -> Decimal:
    """Discounted subtotal, plus tax, plus shipping decided on the discounted subtotal."""
    discounted = apply_discount(cart.subtotal(), discount_percent)
    return add_tax(discounted, rate_for(state)) + shipping_cost(discounted)
