from __future__ import annotations

import re
from typing import Callable, Iterable, Optional, Tuple

import win32com.client  # pywin32
import ipinfo

SIG_RE = re.compile(r"^\s*(sig-name|sname)\s*:\s*(.*)\s*$", re.IGNORECASE)
SRC_RE = re.compile(r"^\s*src\s*:\s*$", re.IGNORECASE)
IP_RE = re.compile(r"^\s*ip\s*:\s*(.*)\s*$", re.IGNORECASE)


def parse_fireeye_email_body(body: str) -> Tuple[str, str, str]:
    """
    Extract (sig_name, src_ip, dst_ip) from a FireEye alert email body.

    Preserves the original ordering/state-machine behavior:
      - When a line matches 'src:', the next 'ip:' is treated as src_ip
      - The following 'ip:' (when not expecting src) is treated as dst_ip
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


def iter_alert_lines(
    unread_items: Iterable,
    ipinfo_handler: Optional[ipinfo.Handler],
    ip_lookup_fn: Callable[[ipinfo.Handler, str], Optional[str]],
):
    """
    Yield formatted lines for the summary file, and mark messages read.

    ip_lookup_fn is injected to keep parsing separate from enrichment logic.
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

        # Mark read (original behavior)
        try:
            msg.Unread = False
        except Exception:
            pass
