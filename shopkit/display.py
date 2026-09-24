import humanize


def money(amount) -> str:
    """Dollar amount with thousands separators: 1234.5 -> $1,234.50."""
    return "$" + humanize.intcomma(amount, 2)
