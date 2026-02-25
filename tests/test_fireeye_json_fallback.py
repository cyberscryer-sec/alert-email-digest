import json
from pathlib import Path

from parsers.fireeye import parse_fireeye_email_body


def test_json_fixture_parses_sig_src_dst():
    fixture = Path("examples/fireeye_json/alert_sql_injection.json").read_text(encoding="utf-8")
    sig, src, dst = parse_fireeye_email_body(fixture)

    assert sig == "SQL Injection Attempt"
    assert src == "203.0.113.45"
    assert dst == "198.51.100.10"


def test_json_inline_string_parses():
    payload = {
        "msg": "normal",
        "product": "CMS",
        "alert": {
            "src": {"ip": "203.0.113.9"},
            "dst": {"ip": "198.51.100.88"},
            "explanation": {"ips-detected": {"sig-name": "Test Signature"}},
        },
    }
    sig, src, dst = parse_fireeye_email_body(json.dumps(payload))
    assert sig == "Test Signature"
    assert src == "203.0.113.9"
    assert dst == "198.51.100.88"
