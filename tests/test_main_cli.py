import datetime as dt
import json

import main as cli


class FakeOutlookItem:
    def __init__(self):
        self.Subject = "FireEye Alert - Test"
        self.Body = """sig-name: Test Alert
src:
ip: 203.0.113.45
ip: 198.51.100.10
"""
        self.SentOn = dt.datetime(2026, 2, 22, 11, 30, 0)
        self.EntryID = "entry-1"
        self.Unread = True


def test_demo_cli_writes_text_and_json(tmp_path):
    text_out = tmp_path / "summary.txt"
    json_out = tmp_path / "summary.json"

    result = cli.main(
        [
            "--demo",
            "--source",
            "fireeye",
            "--no-ipinfo",
            "--output",
            str(text_out),
            "--json-output",
            str(json_out),
        ]
    )

    assert result == 0
    text = text_out.read_text(encoding="utf-8")
    data = json.loads(json_out.read_text(encoding="utf-8"))
    assert "FireEye Demo" in text
    assert "SQL Injection Attempt" in text
    assert "Possible Malware Callback" in text
    assert data["record_count"] == 2
    assert data["alerts"][0]["source"] == "fireeye"


def test_outlook_mode_marks_read_by_default(monkeypatch, tmp_path):
    item = FakeOutlookItem()
    monkeypatch.setattr(cli, "get_unread_items", lambda *_args: [item])

    cli.main(["--no-ipinfo", "--output", str(tmp_path / "summary.txt")])

    assert item.Unread is False


def test_outlook_mode_can_skip_mark_read(monkeypatch, tmp_path):
    item = FakeOutlookItem()
    monkeypatch.setattr(cli, "get_unread_items", lambda *_args: [item])

    cli.main(
        [
            "--no-ipinfo",
            "--no-mark-read",
            "--output",
            str(tmp_path / "summary.txt"),
        ]
    )

    assert item.Unread is True
