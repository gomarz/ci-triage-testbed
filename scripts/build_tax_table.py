"""Turn data/tax_rates.csv into build/tax_rates.json for shopkit.tax."""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    with (ROOT / "data" / "tax_rates.csv").open(newline="", encoding="utf-8") as f:
        rates = {row["state"]: row["rate"] for row in csv.DictReader(f)}
    out = ROOT / "build" / "tax_rates.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(rates, indent=2), encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)} ({len(rates)} states)")


if __name__ == "__main__":
    main()
