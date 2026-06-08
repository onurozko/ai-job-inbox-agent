import base64
from datetime import UTC, datetime

from app.integrations.gmail.client import GmailClient


def test_parse_message_extracts_body_sender_and_received_at() -> None:
    body = "Thanks for applying to Shopify."
    encoded_body = base64.urlsafe_b64encode(body.encode()).decode().rstrip("=")
    raw = {
        "id": "abc123",
        "threadId": "thread-abc",
        "snippet": "Thanks for applying",
        "internalDate": str(int(datetime(2026, 6, 5, 12, 0, tzinfo=UTC).timestamp() * 1000)),
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Application received"},
                {"name": "From", "value": "Shopify Recruiting <jobs@shopify.com>"},
            ],
            "mimeType": "text/plain",
            "body": {"data": encoded_body},
        },
    }

    parsed = GmailClient.parse_message(raw)

    assert parsed.gmail_message_id == "abc123"
    assert parsed.thread_id == "thread-abc"
    assert parsed.subject == "Application received"
    assert parsed.sender_email == "jobs@shopify.com"
    assert parsed.body_text == body
    assert parsed.received_at == datetime(2026, 6, 5, 12, 0, tzinfo=UTC)
