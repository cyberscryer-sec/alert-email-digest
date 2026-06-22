import datetime as dt
from pathlib import Path

from models import EmailMessage
from parsers.fireeye import FireEyeParser


def test_fireeye_parser_returns_normalized_record_from_json():
    body = Path("examples/fireeye_json/alert_sql_injection.json").read_text(
        encoding="utf-8"
    )
    message = EmailMessage(
        subject="FireEye Alert - SQL Injection Attempt",
        body=body,
        sent_on=dt.datetime(2026, 2, 22, 15, 41, 30),
        message_id="message-1",
    )

    record = FireEyeParser().parse_email(message)

    assert record.source == "fireeye"
    assert record.title == "SQL Injection Attempt"
    assert record.event_time == dt.datetime(2026, 2, 22, 15, 41, 12, tzinfo=dt.timezone.utc)
    assert record.sent_time == dt.datetime(2026, 2, 22, 15, 41, 30)
    assert record.severity == "crit"
    assert record.src_ip == "203.0.113.45"
    assert record.dst_ip == "198.51.100.10"
    assert record.src_port == 54321
    assert record.dst_port == 443
    assert record.host == "NX01"
    assert record.raw_subject == "FireEye Alert - SQL Injection Attempt"
    assert record.raw_id == "ALRT-20260222-0001"
    assert record.details["signature_id"] == "2100017"
    assert record.parse_status == "parsed"


def test_fireeye_parser_returns_unparsed_record_for_unknown_body():
    message = EmailMessage(
        subject="Unmatched alert",
        body="nothing useful here",
        message_id="message-2",
    )

    record = FireEyeParser().parse_email(message)

    assert record.source == "fireeye"
    assert record.title == ""
    assert record.src_ip == ""
    assert record.dst_ip == ""
    assert record.raw_subject == "Unmatched alert"
    assert record.raw_id == "message-2"
    assert record.parse_status == "unparsed"
