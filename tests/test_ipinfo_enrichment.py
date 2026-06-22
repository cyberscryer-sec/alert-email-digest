from enrich.ipinfo_enrichment import safe_ipinfo_lookup


class RaisingHandler:
    def getDetails(self, _ip):
        raise AssertionError("lookup should not be called")


class FakeDetails:
    all = {
        "city": "Los Angeles",
        "country_name": "United States",
        "org": "ExampleOrg",
    }


class FakeHandler:
    def __init__(self):
        self.seen_ip = None

    def getDetails(self, ip):
        self.seen_ip = ip
        return FakeDetails()


def test_safe_ipinfo_lookup_skips_blank_invalid_and_private_ips():
    handler = RaisingHandler()

    assert safe_ipinfo_lookup(handler, "") is None
    assert safe_ipinfo_lookup(handler, "not-an-ip") is None
    assert safe_ipinfo_lookup(handler, "10.20.30.40") is None
    assert safe_ipinfo_lookup(handler, "203.0.113.45") is None


def test_safe_ipinfo_lookup_returns_attribution_for_global_ip():
    handler = FakeHandler()

    result = safe_ipinfo_lookup(handler, "8.8.8.8")

    assert handler.seen_ip == "8.8.8.8"
    assert result == "from Los Angeles, United States (ExampleOrg)"
