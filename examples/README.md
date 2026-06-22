These example alert payloads are fully synthetic and contain no real company,
customer, or production data. IPs use documentation ranges (RFC 5737) and
private ranges (RFC 1918).

`fireeye_json/` contains raw synthetic FireEye-style JSON bodies used by parser
unit tests.

`demo_emails/` contains small `.eml` and `.txt` samples for simulating a run
without connecting to Outlook:

```powershell
python main.py --demo --source fireeye --no-ipinfo
```
