"""
fireeye_digest.py

Parse unread FireEye alert emails from an Outlook folder and write a daily summary.

Example:
  set IPINFO_TOKEN=xxxx
  set OUTLOOK_MAILBOX=your.name@example.com
  python fireeye_digest.py --region East --output out/summary_2026-02-22.txt
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
from pathlib import Path
from typing import Iterable, Optional, Tuple

import win32com.client  # pywin32
import ipinfo


SIG_RE = re.compile(r"^\s*(sig-name|sname)\s*:\s*(.*)\s*$", re.IGNORECASE)
SRC_RE = re.compile(r"^\s*src\s*:\s*$", re.IGNORECASE)
IP_RE = re.compile(r"^\s*ip\s*:\s*(.*)\s*$", re.IGNORECASE)


def parse_fireeye_email_body(body: str) -> Tuple[str, str, str]:
    """
    Extract (sig_name, src_ip, dst_ip) from a FireEye alert email body.
    This is based on the original script’s parsing rules.
    """
    sig_name = ""
    src_ip = ""
    dst_ip = ""
    expecting_src_ip = False

    for line in body.splitlines():
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


def safe_ipinfo_lookup(handler: ipinfo.Handler, ip: str) -> Optional[str]:
    """
    Return a short human-readable attribution string or None if unknown/unavailable.
    """
    # Basic IP sanity check (keeps us from calling ipinfo on blanks/garbage)
    if not re.match(r"^\d{1,3}(\.\d{1,3}){3}$", ip):
        return None

    try:
        details = handler.getDetails(ip).all
    except Exception:
        return None

    city = details.get("city") or ""
    country = details.get("country_name") or ""
    org = details.get("org") or ""
    out = f"from {city}, {country} ({org})".strip()

    # If it came back empty-ish, treat as unknown
    normalized = out.replace(" ", "")
    if "from,()" in normalized or normalized in {"from,()", "from,()"}:
        return None

    return out


def get_outlook_namespace():
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


def iter_alert_lines(unread_items: Iterable, ipinfo_handler: Optional[ipinfo.Handler]):
    """
    Yield formatted lines for the summary file, and mark messages read.
    """
    for msg in unread_items:
        body = getattr(msg, "Body", "") or ""
        sent_on = getattr(msg, "SentOn", None)
        sent_time = sent_on.time() if sent_on else None

        sig_name, src_ip, dst_ip = parse_fireeye_email_body(body)

        # Build summary
        time_str = str(sent_time) if sent_time else "UnknownTime"
        yield f"{time_str}: {sig_name or 'UnknownSig'} - {dst_ip or 'UnknownDst'}\n"
        yield f"\t\tSource: {src_ip or 'UnknownSrc'}\n"

        if ipinfo_handler and src_ip:
            attribution = safe_ipinfo_lookup(ipinfo_handler, src_ip.strip())
            yield f"\t\t{attribution if attribution else 'UNIDENTIFIED'}\n"
        else:
            yield "\t\tUNIDENTIFIED\n"

        # Mark read (original behavior)
        try:
            msg.Unread = False
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser(description="Generate daily summary from Outlook FireEye alert emails.")
    parser.add_argument("--mailbox", default=os.getenv("OUTLOOK_MAILBOX", "user@example.com"),
                        help="Outlook mailbox display name/email (env: OUTLOOK_MAILBOX).")
    parser.add_argument("--fireeye-root", default=os.getenv("FIREEYE_FOLDER", "FireEye"),
                        help="Name of the FireEye folder under the mailbox (env: FIREEYE_FOLDER).")
    parser.add_argument("--region", default="East", help="Region subfolder under FireEye (e.g., East, West).")
    parser.add_argument("--output", default=None, help="Output file path. Default: out/summary_YYYY-MM-DD.txt")
    parser.add_argument("--no-ipinfo", action="store_true", help="Disable ipinfo enrichment.")
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
        for line in iter_alert_lines(unread, ipinfo_handler):
            f.write(line)
        f.write("------------------------------------\n")

    print(f"Wrote: {out_path}")


if __name__ == "__main__":
    main()
