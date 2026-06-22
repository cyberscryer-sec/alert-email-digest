from __future__ import annotations

import ipaddress
from typing import Any, Optional


def safe_ipinfo_lookup(handler: Any, ip: str) -> Optional[str]:
    """
    Return a short human-readable attribution string or None if unknown/unavailable.
    """
    try:
        address = ipaddress.ip_address(ip)
    except ValueError:
        return None

    if not address.is_global:
        return None

    try:
        details = handler.getDetails(ip).all
    except Exception:
        return None

    city = details.get("city") or ""
    country = details.get("country_name") or ""
    org = details.get("org") or ""
    out = f"from {city}, {country} ({org})".strip()

    normalized = out.replace(" ", "")
    if "from,()" in normalized or normalized in {"from,()", "from,()"}:
        return None

    return out
