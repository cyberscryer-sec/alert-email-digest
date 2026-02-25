from parsers.fireeye import parse_fireeye_email_body


def test_sig_name_extraction():
    body = "sig-name: SQL Injection Attempt\n"
    sig, src, dst = parse_fireeye_email_body(body)
    assert sig == "SQL Injection Attempt"


def test_source_ip_ordering():
    body = """sig-name: Test Alert
src:
ip: 203.0.113.45
ip: 198.51.100.10
"""
    sig, src, dst = parse_fireeye_email_body(body)
    assert src == "203.0.113.45"
    assert dst == "198.51.100.10"


def test_missing_fields():
    body = "unrelated text\n"
    sig, src, dst = parse_fireeye_email_body(body)
    assert sig == ""
    assert src == ""
    assert dst == ""
