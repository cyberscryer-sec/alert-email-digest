from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol


MarkReadFn = Callable[[], None]


@dataclass
class EmailMessage:
    subject: str = ""
    body: str = ""
    sent_on: dt.datetime | None = None
    message_id: str = ""
    _mark_read: MarkReadFn | None = field(default=None, repr=False, compare=False)

    def mark_read(self) -> None:
        if self._mark_read:
            self._mark_read()


@dataclass
class AlertRecord:
    source: str
    title: str = ""
    event_time: dt.datetime | None = None
    sent_time: dt.datetime | None = None
    severity: str = ""
    src_ip: str = ""
    dst_ip: str = ""
    src_port: int | None = None
    dst_port: int | None = None
    host: str = ""
    user: str = ""
    raw_subject: str = ""
    raw_id: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    parse_status: str = "parsed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "title": self.title,
            "event_time": _datetime_to_iso(self.event_time),
            "sent_time": _datetime_to_iso(self.sent_time),
            "severity": self.severity,
            "src_ip": self.src_ip,
            "dst_ip": self.dst_ip,
            "src_port": self.src_port,
            "dst_port": self.dst_port,
            "host": self.host,
            "user": self.user,
            "raw_subject": self.raw_subject,
            "raw_id": self.raw_id,
            "details": self.details,
            "parse_status": self.parse_status,
        }


class AlertParser(Protocol):
    source: str
    display_name: str

    def parse_email(self, message: EmailMessage) -> AlertRecord:
        ...


def _datetime_to_iso(value: dt.datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()
