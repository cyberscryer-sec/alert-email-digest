from __future__ import annotations

import datetime as dt
import json
import re
from typing import Any, Callable, Iterable, Optional, Tuple

from models import AlertRecord, EmailMessage

SIG_RE = re.compile(r"^\s*(sig-name|sname)\s*:\s*(.*)\s*$", re.IGNORECASE)
SRC_RE = re.compile(r"^\s*src\s*:\s*$", re.IGNORECASE)
IP_RE = re.compile(r"^\s*ip\s*:\s*(.*)\s*$", re.IGNORECASE)


def parse_fireeye_email_body(body: str) -> Tuple[str, str, str]:
    """
    Extract (sig_name, src_ip, dst_ip) from a FireEye alert email body.

    Behavior:
      1) Try JSON parsing first (common FireEye notification formats).
      2) If not JSON, fall back to the original ordering/state-machine:
         - 'src:' sets a flag
         - next 'ip:' becomes src_ip
         - next 'ip:' becomes dst_ip
    """
    fields = _parse_fireeye_json(body)
    if fields:
        return fields["title"], fields["src_ip"], fields["dst_ip"]

    sig_name = ""
    src_ip = ""
    dst_ip = ""
    expecting_src_ip = False

    for line in (body or "").splitlines():
        m = SIG_RE.match(line)
        if m:
            sig_name = m.group(2).strip()
            continue

        if SRC_RE.match(line):
            expecting_src_ip = True
            continue

        m = IP_RE.match(line)
        if m:
            ip_val = m.group(1).strip()
            if expecting_src_ip:
                src_ip = ip_val
                expecting_src_ip = False
            else:
                dst_ip = ip_val

    return sig_name, src_ip, dst_ip


class FireEyeParser:
    source = "fireeye"
    display_name = "FireEye"

    def parse_email(self, message: EmailMessage) -> AlertRecord:
        fields = _parse_fireeye_json(message.body)

        if fields:
            title = fields["title"]
            src_ip = fields["src_ip"]
            dst_ip = fields["dst_ip"]
            details = {
                "parser": self.source,
                "product": fields["product"],
                "direction": fields["direction"],
                "signature_id": fields["signature_id"],
            }
            details = {key: value for key, value in details.items() if value}
            return AlertRecord(
                source=self.source,
                title=title,
                event_time=fields["event_time"],
                sent_time=message.sent_on,
                severity=fields["severity"],
                src_ip=src_ip,
                dst_ip=dst_ip,
                src_port=fields["src_port"],
                dst_port=fields["dst_port"],
                host=fields["sensor"],
                raw_subject=message.subject,
                raw_id=fields["alert_id"] or message.message_id,
                details=details,
                parse_status=_parse_status(title, src_ip, dst_ip),
            )

        sig_name, src_ip, dst_ip = parse_fireeye_email_body(message.body)
        return AlertRecord(
            source=self.source,
            title=sig_name,
            sent_time=message.sent_on,
            src_ip=src_ip,
            dst_ip=dst_ip,
            raw_subject=message.subject,
            raw_id=message.message_id,
            details={"parser": self.source},
            parse_status=_parse_status(sig_name, src_ip, dst_ip),
        )


def get_outlook_namespace():
    import win32com.client  # pywin32

    return win32com.client.Dispatch("Outlook.Application").GetNameSpace("MAPI")


def get_unread_items(mailbox: str, fireeye_root: str, region: str):
    """
    Locate mailbox -> FireEye folder -> region folder and return unread items.
    """
    outlook = get_outlook_namespace()
    root_folder = outlook.Folders[mailbox]
    fireeye_folder = root_folder.Folders[fireeye_root]
    region_folder = fireeye_folder.Folders[region]
    return region_folder.Items.Restrict("[Unread] = true")


def iter_alert_lines(
    unread_items: Iterable,
    ipinfo_handler: Optional[Any],
    ip_lookup_fn: Callable[[Any, str], Optional[str]],
):
    """
    Yield formatted lines for the summary file, and mark messages read.
    """
    for msg in unread_items:
        body = getattr(msg, "Body", "") or ""
        sent_on = getattr(msg, "SentOn", None)
        sent_time = sent_on.time() if sent_on else None

        sig_name, src_ip, dst_ip = parse_fireeye_email_body(body)

        time_str = str(sent_time) if sent_time else "UnknownTime"
        yield f"{time_str}: {sig_name or 'UnknownSig'} - {dst_ip or 'UnknownDst'}\n"
        yield f"\t\tSource: {src_ip or 'UnknownSrc'}\n"

        if ipinfo_handler and src_ip:
            attribution = ip_lookup_fn(ipinfo_handler, src_ip.strip())
            yield f"\t\t{attribution if attribution else 'UNIDENTIFIED'}\n"
        else:
            yield "\t\tUNIDENTIFIED\n"

        try:
            msg.Unread = False
        except Exception:
            pass


def _parse_fireeye_json(body: str) -> dict[str, Any] | None:
    text = (body or "").strip()
    if not text.startswith("{") or not text.endswith("}"):
        return None

    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None

    if not isinstance(payload, dict):
        return None

    alert = payload.get("alert", {})
    if not isinstance(alert, dict):
        return None

    src = alert.get("src", {})
    dst = alert.get("dst", {})
    metadata = alert.get("metadata", {})
    explanation = alert.get("explanation", {})
    ips_detected = {}

    if isinstance(explanation, dict):
        ips_detected = explanation.get("ips-detected", {})
    if not isinstance(ips_detected, dict):
        ips_detected = {}

    fields = {
        "title": _coerce_str(ips_detected.get("sig-name")),
        "src_ip": _coerce_str(src.get("ip") if isinstance(src, dict) else ""),
        "dst_ip": _coerce_str(dst.get("ip") if isinstance(dst, dict) else ""),
        "src_port": _coerce_int(src.get("port") if isinstance(src, dict) else None),
        "dst_port": _coerce_int(dst.get("port") if isinstance(dst, dict) else None),
        "event_time": _parse_datetime(alert.get("occurred")),
        "severity": _coerce_str(alert.get("severity")),
        "product": _coerce_str(payload.get("product")),
        "sensor": _coerce_str(metadata.get("sensor") if isinstance(metadata, dict) else ""),
        "alert_id": _coerce_str(metadata.get("alert-id") if isinstance(metadata, dict) else ""),
        "direction": _coerce_str(metadata.get("direction") if isinstance(metadata, dict) else ""),
        "signature_id": _coerce_str(ips_detected.get("sig-id")),
    }

    if fields["title"] or fields["src_ip"] or fields["dst_ip"]:
        return fields
    return None


def _parse_datetime(value: Any) -> dt.datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return dt.datetime.fromisoformat(text)
    except ValueError:
        return None


def _coerce_str(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _coerce_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_status(title: str, src_ip: str, dst_ip: str) -> str:
    return "parsed" if title or src_ip or dst_ip else "unparsed"
