from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")


def apply_discount(price: Decimal, percent: int) -> Decimal:
    """Price after `percent` off, rounded half up to the cent.

    Half up, not banker's rounding: 1.25 at 50% off is 0.63, which is what the
    printed price list shows customers.
    """
    if not 0 <= percent <= 100:
        raise ValueError(f"discount must be 0-100, got {percent}")
    return (price * (100 - percent) / 100).quantize(CENT, rounding=ROUND_HALF_UP)


def add_tax(amount: Decimal, rate_percent: Decimal) -> Decimal:
    """Amount plus tax at `rate_percent`, rounded half up to the cent."""
    return (amount * (100 + rate_percent) / 100).quantize(CENT, rounding=ROUND_HALF_UP)
