# alert-email-digest

![CI](https://github.com/cyberscryer-sec/alert-email-digest/actions/workflows/ci.yml/badge.svg)

Python tool for parsing security alert email notifications and generating
structured daily incident summaries.

This project automates analyst triage workflows in environments where security
alerts are delivered by email. It normalizes key alert fields, including alert
title, source IP, destination IP, severity, and timestamps, then writes a daily
timeline for operational visibility and handoff.

All examples and test fixtures in this repository are synthetic and contain no
real customer, company, or production data.

## Features

- Parses unread FireEye-style alert notifications from Microsoft Outlook.
- Preserves the original FireEye body parsing logic:
  `src:` followed by the next `ip:` is treated as the source IP.
- Supports JSON-style FireEye alert bodies and legacy text-style alert bodies.
- Normalizes parsed alerts into a shared `AlertRecord` model.
- Writes the existing daily text summary format.
- Optionally writes structured JSON output for downstream processing.
- Supports optional IP attribution via ipinfo.
- Marks Outlook messages as read after successful processing by default.
- Provides a synthetic demo mode that does not require Outlook access.
- Keeps parser logic modular so additional alert sources can be added later.

## Project Structure

```text
alert-email-digest/
|-- main.py
|-- models.py
|-- inputs.py
|-- renderers.py
|-- parsers/
|   |-- __init__.py
|   `-- fireeye.py
|-- enrich/
|   |-- __init__.py
|   `-- ipinfo_enrichment.py
|-- examples/
|   |-- demo_emails/
|   `-- fireeye_json/
|-- tests/
|-- requirements.txt
|-- .env.example
`-- README.md
```

## Requirements

- Windows OS for Outlook COM automation
- Microsoft Outlook installed and configured
- Python 3.10+
- Python dependencies from `requirements.txt`

`pywin32` is only needed for live Outlook collection. Parser tests and demo
sample parsing do not launch Outlook.

## Installation

```powershell
git clone https://github.com/cyberscryer-sec/alert-email-digest.git
cd alert-email-digest
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

Store sensitive values in environment variables.

```powershell
$env:OUTLOOK_MAILBOX="user@example.com"
$env:FIREEYE_FOLDER="FireEye"
$env:IPINFO_TOKEN="your_token_here"
```

`IPINFO_TOKEN` is optional. If it is missing, summaries still run and source
attribution lines show `UNIDENTIFIED`.

## Outlook Usage

Process unread FireEye alerts from the default mailbox, FireEye root folder,
and `East` region subfolder:

```powershell
python main.py --region East
```

Specify the output file:

```powershell
python main.py --region East --output out/summary_2026-02-22.txt
```

Write text and JSON summaries in one run:

```powershell
python main.py `
  --region East `
  --output out/summary_2026-02-22.txt `
  --json-output out/summary_2026-02-22.json
```

Disable IP enrichment:

```powershell
python main.py --region East --no-ipinfo
```

Run a dry pass without marking Outlook messages as read:

```powershell
python main.py --region East --no-mark-read --no-ipinfo
```

Override mailbox and folder names:

```powershell
python main.py `
  --mailbox "user@example.com" `
  --fireeye-root "FireEye" `
  --region East
```

## Demo Usage

To simulate how the tool processes alert emails without connecting to Outlook,
run the synthetic demo samples:

```powershell
python main.py --demo --source fireeye --no-ipinfo
```

Demo mode reads from `examples/demo_emails/` by default. You can also point the
tool at any directory containing synthetic `.eml`, `.json`, or `.txt` samples:

```powershell
python main.py `
  --input-dir examples/demo_emails `
  --source fireeye `
  --no-ipinfo `
  --json-output out/demo_summary.json
```

## Example Text Output

```text
FireEye East

15:41:12: SQL Injection Attempt - 198.51.100.10
        Source: 203.0.113.45
        UNIDENTIFIED
18:07:03: Possible Malware Callback - 203.0.113.200
        Source: 10.20.30.40
        UNIDENTIFIED
------------------------------------
```

## Parser Architecture

The CLI uses an adapter-style parser contract:

- `EmailMessage` represents the source email, regardless of Outlook or file
  input.
- `AlertParser` defines `parse_email(message) -> AlertRecord`.
- `AlertRecord` is the normalized alert model used by text and JSON renderers.
- `FireEyeParser` wraps the existing FireEye parsing rules and adds normalized
  metadata fields.

The original compatibility function remains available:

```python
from parsers.fireeye import parse_fireeye_email_body

sig_name, src_ip, dst_ip = parse_fireeye_email_body(body)
```

## Testing

Run the test suite:

```powershell
pytest
```

Tests cover:

- FireEye legacy text parsing.
- FireEye JSON fallback parsing.
- Normalized `AlertRecord` generation.
- Synthetic demo file loading.
- Text and JSON rendering.
- Outlook mark-read and `--no-mark-read` behavior using fake messages.
- ipinfo lookup safety for blank, invalid, private, and documentation IPs.

## Security Considerations

- Do not commit real email exports.
- Do not commit API tokens.
- Use environment variables for secrets.
- Keep examples synthetic.
- Review generated summaries before sharing outside the operational context.

## Roadmap

- Add a Wazuh email alert parser.
- Add an AWS GuardDuty JSON/SNS-style parser.
- Add a Microsoft Defender XDR parser once representative email samples are
  available.
- Add structured logging for collection and parsing status.
