from __future__ import annotations

import re
from typing import Callable, Iterable, Optional, Tuple

import ipinfo
import win32com.client  # pywin32

import json
from typing import Any

SIG_RE = re.compile(r"^\s*(sig-name|sname)\s*:\s*(.*)\s*$", re.IGNORECASE)
SRC_RE = re.compile(r"^\s*src\s*:\s*$", re.IGNORECASE)
IP_RE = re.compile(r"^\s*ip\s*:\s*(.*)\s*$", re.IGNORECASE)


def _get_nested(d: dict, path: tuple[str, ...]) -> str:
    cur: Any = d
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return ""
        cur = cur[key]
    return cur if isinstance(cur, str) else ""


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
    # --- 1) In-line JSON-first attempt ---
    text = (body or "").strip()
    if text.startswith("{") and text.endswith("}"):
        try:
            payload = json.loads(text)
            alert = payload.get("alert", {}) if isinstance(payload, dict) else {}

            src_ip = ""
            dst_ip = ""
            sig_name = ""

            src = alert.get("src", {}) if isinstance(alert, dict) else {}
            dst = alert.get("dst", {}) if isinstance(alert, dict) else {}
            if isinstance(src, dict):
                src_ip = (src.get("ip") or "").strip()
            if isinstance(dst, dict):
                dst_ip = (dst.get("ip") or "").strip()

            # Common documented location from your fixture template:
            # alert.explanation.ips-detected.sig-name
            explanation = alert.get("explanation", {}) if isinstance(alert, dict) else {}
            if isinstance(explanation, dict):
                ips_detected = explanation.get("ips-detected", {})
                if isinstance(ips_detected, dict):
                    sig_name = (ips_detected.get("sig-name") or "").strip()

            if sig_name or src_ip or dst_ip:
                return sig_name, src_ip, dst_ip
        except Exception:
            pass

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
