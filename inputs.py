from __future__ import annotations

from email import policy
from email.parser import BytesParser
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Iterable

from models import EmailMessage


SUPPORTED_INPUT_SUFFIXES = {".eml", ".json", ".txt"}


def load_file_messages(input_dir: Path) -> list[EmailMessage]:
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input path is not a directory: {input_dir}")

    messages: list[EmailMessage] = []
    for path in sorted(input_dir.iterdir()):
        if path.is_file() and path.suffix.lower() in SUPPORTED_INPUT_SUFFIXES:
            messages.append(load_file_message(path))
    return messages


def load_file_message(path: Path) -> EmailMessage:
    if path.suffix.lower() == ".eml":
        return _load_eml_message(path)

    return EmailMessage(
        subject=path.stem,
        body=path.read_text(encoding="utf-8"),
        message_id=path.name,
    )


def outlook_items_to_messages(items: Iterable) -> list[EmailMessage]:
    return [outlook_item_to_email_message(item) for item in items]


def outlook_item_to_email_message(item) -> EmailMessage:
    def mark_read() -> None:
        try:
            item.Unread = False
        except Exception:
            pass

    return EmailMessage(
        subject=getattr(item, "Subject", "") or "",
        body=getattr(item, "Body", "") or "",
        sent_on=getattr(item, "SentOn", None),
        message_id=str(getattr(item, "EntryID", "") or ""),
        _mark_read=mark_read,
    )


def _load_eml_message(path: Path) -> EmailMessage:
    with path.open("rb") as f:
        parsed = BytesParser(policy=policy.default).parse(f)

    sent_on = None
    if parsed.get("Date"):
        try:
            sent_on = parsedate_to_datetime(parsed["Date"])
        except (TypeError, ValueError):
            sent_on = None

    return EmailMessage(
        subject=parsed.get("Subject", "") or path.stem,
        body=_extract_plain_text(parsed),
        sent_on=sent_on,
        message_id=parsed.get("Message-ID", "") or path.name,
    )


def _extract_plain_text(parsed) -> str:
    if parsed.is_multipart():
        for part in parsed.walk():
            if part.get_content_type() == "text/plain":
                disposition = part.get_content_disposition()
                if disposition != "attachment":
                    return part.get_content()
        return ""

    content = parsed.get_content()
    return content if isinstance(content, str) else ""
