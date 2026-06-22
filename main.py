"""
main.py

CLI entry point for generating daily summaries from security alert emails.

Example:
  set IPINFO_TOKEN=xxxx
  set OUTLOOK_MAILBOX=your.name@example.com
  python main.py --region East --output out/summary_2026-02-22.txt
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
from pathlib import Path

from enrich.ipinfo_enrichment import safe_ipinfo_lookup
from inputs import load_file_messages, outlook_items_to_messages
from models import AlertParser, AlertRecord, EmailMessage
from parsers.fireeye import FireEyeParser, get_unread_items
from renderers import write_json_summary, write_text_summary


PARSER_REGISTRY = {
    "fireeye": FireEyeParser,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate daily summaries from security alert emails."
    )
    parser.add_argument(
        "--source",
        default="fireeye",
        choices=sorted(PARSER_REGISTRY),
        help="Alert source/parser to use.",
    )
    parser.add_argument(
        "--mailbox",
        default=os.getenv("OUTLOOK_MAILBOX", "user@example.com"),
        help="Outlook mailbox display name/email (env: OUTLOOK_MAILBOX).",
    )
    parser.add_argument(
        "--fireeye-root",
        default=os.getenv("FIREEYE_FOLDER", "FireEye"),
        help="Name of the FireEye folder under the mailbox (env: FIREEYE_FOLDER).",
    )
    parser.add_argument(
        "--region",
        default="East",
        help="Region subfolder under FireEye (e.g., East, West).",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output file path. Default: out/summary_YYYY-MM-DD.txt",
    )
    parser.add_argument(
        "--json-output",
        default=None,
        help="Optional structured JSON output path.",
    )
    parser.add_argument(
        "--no-ipinfo",
        action="store_true",
        help="Disable ipinfo enrichment.",
    )
    parser.add_argument(
        "--no-mark-read",
        action="store_true",
        help="Do not mark Outlook messages as read after processing.",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Parse synthetic demo email samples from examples/demo_emails.",
    )
    parser.add_argument(
        "--input-dir",
        default=None,
        help="Parse .eml, .json, and .txt samples from a directory instead of Outlook.",
    )
    args = parser.parse_args(argv)

    today = dt.date.today().isoformat()
    out_path = Path(args.output) if args.output else Path("out") / f"summary_{today}.txt"
    json_path = Path(args.json_output) if args.json_output else None

    alert_parser = build_parser(args.source)
    messages, can_mark_read = collect_messages(args)
    records = parse_messages(messages, alert_parser)
    enrich_records(records, args.no_ipinfo)

    write_text_summary(out_path, records, build_heading(alert_parser, args))
    if json_path:
        write_json_summary(json_path, records)

    if can_mark_read and not args.no_mark_read:
        for message in messages:
            message.mark_read()

    print(f"Wrote: {out_path}")
    if json_path:
        print(f"Wrote: {json_path}")
    print(f"Processed {len(records)} alert(s).")
    return 0


def build_parser(source: str) -> AlertParser:
    return PARSER_REGISTRY[source]()


def collect_messages(args: argparse.Namespace) -> tuple[list[EmailMessage], bool]:
    if args.demo or args.input_dir:
        input_dir = (
            Path(args.input_dir)
            if args.input_dir
            else Path("examples") / "demo_emails"
        )
        return load_file_messages(input_dir), False

    unread = get_unread_items(args.mailbox, args.fireeye_root, args.region)
    return outlook_items_to_messages(unread), True


def parse_messages(
    messages: list[EmailMessage],
    alert_parser: AlertParser,
) -> list[AlertRecord]:
    return [alert_parser.parse_email(message) for message in messages]


def enrich_records(records: list[AlertRecord], no_ipinfo: bool) -> None:
    handler = build_ipinfo_handler(no_ipinfo)
    if handler is None:
        return

    for record in records:
        if not record.src_ip:
            continue
        attribution = safe_ipinfo_lookup(handler, record.src_ip.strip())
        if attribution:
            record.details["source_attribution"] = attribution


def build_ipinfo_handler(no_ipinfo: bool):
    if no_ipinfo:
        return None

    token = os.getenv("IPINFO_TOKEN", "").strip()
    if not token:
        return None

    import ipinfo

    return ipinfo.getHandler(token)


def build_heading(alert_parser: AlertParser, args: argparse.Namespace) -> str:
    if args.demo:
        return f"{alert_parser.display_name} Demo"
    return f"{alert_parser.display_name} {args.region}"


if __name__ == "__main__":
    raise SystemExit(main())
