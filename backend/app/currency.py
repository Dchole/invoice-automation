"""Currency conversion utility."""
from __future__ import annotations
from app.config import settings


def convert(amount: float, from_currency: str, to_currency: str) -> float:
    """Convert amount between currencies. Returns rounded to 2 decimal places."""
    if from_currency == to_currency:
        return amount

    from_c = from_currency.upper()
    to_c = to_currency.upper()

    # Convert to CAD first (base currency), then to target
    if from_c == "CAD" and to_c == "USD":
        return round(amount * settings.cad_to_usd, 2)
    elif from_c == "USD" and to_c == "CAD":
        return round(amount * settings.usd_to_cad, 2)
    else:
        # Unsupported pair — return as-is
        return amount
