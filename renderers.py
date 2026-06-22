from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from models import AlertRecord


def sort_records(records: list[AlertRecord]) -> list[AlertRecord]:
    return sorted(records, key=_record_sort_key)


def format_text_summary(records: list[AlertRecord], heading: str) -> str:
    lines = ["", heading]

    for record in sort_records(records):
        lines.extend(format_record_lines(record))

    lines.append("------------------------------------")
    return "\n".join(lines) + "\n"


def format_record_lines(record: AlertRecord) -> list[str]:
    attribution = record.details.get("source_attribution") or "UNIDENTIFIED"
    return [
        f"{_time_label(record)}: {record.title or 'UnknownSig'} - "
        f"{record.dst_ip or 'UnknownDst'}",
        f"\t\tSource: {record.src_ip or 'UnknownSrc'}",
        f"\t\t{attribution}",
    ]


def write_text_summary(path: Path, records: list[AlertRecord], heading: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(format_text_summary(records, heading))


def write_json_summary(path: Path, records: list[AlertRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "record_count": len(records),
        "alerts": [record.to_dict() for record in sort_records(records)],
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _record_sort_key(record: AlertRecord) -> dt.datetime:
    value = record.event_time or record.sent_time
    if value is None:
        return dt.datetime.max
    if value.tzinfo is not None:
        return value.astimezone(dt.timezone.utc).replace(tzinfo=None)
    return value


def _time_label(record: AlertRecord) -> str:
    value = record.event_time or record.sent_time
    if value is None:
        return "UnknownTime"
    return value.time().replace(microsecond=0).isoformat()
