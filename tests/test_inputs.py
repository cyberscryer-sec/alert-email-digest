import datetime as dt
from pathlib import Path

from inputs import load_file_messages, outlook_item_to_email_message


class FakeOutlookItem:
    def __init__(self):
        self.Subject = "FireEye Alert"
        self.Body = "sig-name: Test Alert"
        self.SentOn = dt.datetime(2026, 2, 22, 10, 0, 0)
        self.EntryID = "entry-1"
        self.Unread = True


def test_load_file_messages_reads_demo_eml_and_txt():
    messages = load_file_messages(Path("examples/demo_emails"))

    subjects = {message.subject for message in messages}

    assert "FireEye Alert - SQL Injection Attempt" in subjects
    assert "fireeye_malware_callback" in subjects
    assert len(messages) == 2


def test_outlook_item_to_email_message_can_mark_read():
    item = FakeOutlookItem()

    message = outlook_item_to_email_message(item)
    message.mark_read()

    assert message.subject == "FireEye Alert"
    assert message.sent_on == dt.datetime(2026, 2, 22, 10, 0, 0)
    assert item.Unread is False
