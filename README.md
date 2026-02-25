# alert-email-digest

Python tool for parsing security alert email notifications and generating structured daily incident summaries.

This project automates analyst triage workflows in environments where security alerts were delivered via email (pre-SIEM). It normalizes key alert fields (e.g., signature name, source IP, destination IP, timestamp) and produces a clean daily timeline report for operational visibility and handoff.

> All examples and test fixtures in this repository are synthetic and contain no real customer, company, or production data.

---

## 🔍 Features

- Parses FireEye-style alert notification emails from Microsoft Outlook
- Preserves original field ordering logic (`src:` → next `ip:` = source IP)
- Extracts:
  - Signature name (`sig-name` / `sname`)
  - Source IP
  - Destination IP
  - Email sent timestamp
- Generates per-day summary output
- Optional IP enrichment via ipinfo
- Marks processed messages as read (maintains original workflow behavior)
- Modular structure for future parser expansion

---

## 🏗 Project Structure

```
alert-email-digest/
│
├── main.py
├── parsers/
│ ├── __init__.py
│ └── fireeye.py
├── enrich/
│ ├── init.py
│ └── ipinfo_enrichment.py
├── examples/
│ └── fireeye_json/
├── tests/
├── requirements.txt
├── .env.example
├── .gitignore
└── LICENSE
```

### Architecture Overview

- `main.py` → CLI entry point & orchestration
- `parsers/fireeye.py` → FireEye-specific parsing logic
- `enrich/ipinfo_enrichment.py` → External IP attribution logic
- `examples/` → Synthetic alert payloads for demonstration/testing

This separation of concerns allows additional alert formats to be added under `parsers/` without modifying core logic.

---

## 🧰 Requirements

- Windows OS (Outlook COM automation required)
- Microsoft Outlook installed and configured
- Python 3.10+
- Dependencies:
  - `pywin32`
  - `ipinfo`

---

## 📦 Installation

Clone the repository:

```bash
git clone https://github.com/cyberscryer-sec/alert-email-digest.git
cd alert-email-digest
```

Create and activate a virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

## Environment Variables

Store sensitive values in environment variables.

Required:
- `OUTLOOK_MAILBOX` → Outlook mailbox display name/email
- `FIREEYE_FOLDER` → FireEye root folder (default: `FireEye`)
- `IPINFO_TOKEN` → Optional, for IP enrichment
Example (PowerShell):
```Powershell
$env:OUTLOOK_MAILBOX="user@example.com"
$env:FIREEYE_FOLDER="FireEye"
$env:IPINFO_TOKEN="your_token_here"
```
You can also copy .env.example to .env for local development (do NOT commit .env).

## 🚀 Usage

Basic usage:
```bash
python main.py --region East
```
Specify output file:
```bash
python main.py --region East --output out/summary_2026-02-22.txt
```
Disable IP enrichment:
```bash
python main.py --region East --no-ipinfo
```
Override mailbox and folder:
```bash
python main.py \
  --mailbox "user@example.com" \
  --fireeye-root "FireEye" \
  --region East
```

## 📝 Example Output
```
FireEye East

15:41:12: SQL Injection Attempt - 198.51.100.10
        Source: 203.0.113.45
        from Los Angeles, United States (ExampleOrg)

18:07:03: Possible Malware Callback - 203.0.113.200
        Source: 10.20.30.40
        UNIDENTIFIED
------------------------------------
```

## 🧠 How Parsing Works

The FireEye parser preserves the original email field ordering logic observed in production alerts:
1. Detect `sig-name:` or `sname:` lines
2. When `src:` is encountered, the next `ip:` is treated as `src_ip`
3. The subsequent `ip:` (when not expecting a source) is treated as `dst_ip`

## 🧪 Testing 

Examples are located in: `examples/fireeye_json/`. These fixtures simulate realistic FireEye alert payloads using documentation IP ranges (RFC 5737) and contain no sensitive data.

Unit tests validate:
- Signature extraction
- Source/destination IP parsing
- Ordering logic correctness

Run tests:
```bash
pytest
```

## 🔒 Security Considerations

- Do not commit real email exports.
- Do not commit API tokens.
- Use environment variables for secrets.
- Secret scanning and dependency alerts are enabled.

## Roadmap

- Add JSON-first parsing fallback
- Support additional alert email formats
- Output structured JSON alongside text summary
- Add structured logging

## 📄 License
MIT License

---

