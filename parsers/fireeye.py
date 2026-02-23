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
