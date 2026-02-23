def safe_ipinfo_lookup(handler: ipinfo.Handler, ip: str) -> Optional[str]:
    """
    Return a short human-readable attribution string or None if unknown/unavailable.
    """
    # Basic IP sanity check (keeps us from calling ipinfo on blanks/garbage)
    if not re.match(r"^\d{1,3}(\.\d{1,3}){3}$", ip):
        return None

    try:
        details = handler.getDetails(ip).all
    except Exception:
        return None

    city = details.get("city") or ""
    country = details.get("country_name") or ""
    org = details.get("org") or ""
    out = f"from {city}, {country} ({org})".strip()

    # If it came back empty-ish, treat as unknown
    normalized = out.replace(" ", "")
    if "from,()" in normalized or normalized in {"from,()", "from,()"}:
        return None

    return out
