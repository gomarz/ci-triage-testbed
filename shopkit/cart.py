from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Line:
    sku: str
    unit_price: Decimal
    qty: int = 1


class Cart:
    def __init__(self) -> None:
        self._lines: list[Line] = []

    def add(self, line: Line) -> None:
        if line.qty < 1:
            raise ValueError("qty must be at least 1")
        self._lines.append(line)

    @property
    def lines(self) -> tuple[Line, ...]:
        return tuple(self._lines)

    def subtotal(self) -> Decimal:
        return sum((line.unit_price * line.qty for line in self._lines), Decimal("0"))
