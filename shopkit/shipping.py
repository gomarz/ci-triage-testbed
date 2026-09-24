from decimal import Decimal

FREE_SHIPPING_MIN = Decimal("50.00")
FLAT_RATE = Decimal("4.99")


def shipping_cost(subtotal: Decimal) -> Decimal:
    """Free at or above the minimum, a flat rate below it."""
    if subtotal >= FREE_SHIPPING_MIN:
        return Decimal("0.00")
    return FLAT_RATE
