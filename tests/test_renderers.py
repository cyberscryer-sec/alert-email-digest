import datetime as dt
import json

from models import AlertRecord
from renderers import format_text_summary, write_json_summary


def test_text_summary_sorts_by_event_then_sent_time():
    late = AlertRecord(
        source="fireeye",
        title="Late Alert",
        event_time=dt.datetime(2026, 2, 22, 18, 0, 0),
        dst_ip="198.51.100.20",
        src_ip="203.0.113.20",
    )
    early = AlertRecord(
        source="fireeye",
        title="Early Alert",
        sent_time=dt.datetime(2026, 2, 22, 9, 0, 0),
        dst_ip="198.51.100.10",
        src_ip="203.0.113.10",
    )

    text = format_text_summary([late, early], "FireEye East")

    assert text.index("Early Alert") < text.index("Late Alert")
    assert "09:00:00: Early Alert - 198.51.100.10" in text


def test_json_summary_writes_structured_records(tmp_path):
    out_path = tmp_path / "summary.json"
    record = AlertRecord(
        source="fireeye",
        title="Structured Alert",
        event_time=dt.datetime(2026, 2, 22, 12, 0, 0, tzinfo=dt.timezone.utc),
        severity="crit",
        src_ip="203.0.113.45",
        dst_ip="198.51.100.10",
        parse_status="parsed",
    )

    write_json_summary(out_path, [record])

    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert data["record_count"] == 1
    assert data["alerts"][0]["title"] == "Structured Alert"
    assert data["alerts"][0]["event_time"] == "2026-02-22T12:00:00+00:00"
