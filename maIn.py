"""
main.py

CLI entry point for generating a daily summary from Outlook FireEye alert emails.

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

import ipinfo

from enrich.ipinfo_enrichment import safe_ipinfo_lookup
from parsers.fireeye import get_unread_items, iter_alert_lines


def main():
    parser = argparse.ArgumentParser(
        description="Generate daily summary from Outlook FireEye alert emails."
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
        "--no-ipinfo",
        action="store_true",
        help="Disable ipinfo enrichment.",
    )
    args = parser.parse_args()

    today = dt.date.today().isoformat()
    out_path = Path(args.output) if args.output else Path("out") / f"summary_{today}.txt"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    ipinfo_handler = None
    if not args.no_ipinfo:
        token = os.getenv("IPINFO_TOKEN", "").strip()
        if token:
            ipinfo_handler = ipinfo.getHandler(token)

    unread = get_unread_items(args.mailbox, args.fireeye_root, args.region)

    with out_path.open("a", encoding="utf-8") as f:
        f.write(f"\nFireEye {args.region}\n")
        for line in iter_alert_lines(
            unread_items=unread,
            ipinfo_handler=ipinfo_handler,
            ip_lookup_fn=safe_ipinfo_lookup,
        ):
            f.write(line)
        f.write("------------------------------------\n")

    print(f"Wrote: {out_path}")


if __name__ == "__main__":
    main()
