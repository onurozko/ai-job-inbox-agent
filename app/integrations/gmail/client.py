import asyncio
import base64
import email.utils
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

DEFAULT_JOB_SEARCH_QUERY = (
    "newer_than:30d (job OR application OR interview OR recruiter "
    "OR assessment OR offer OR rejected)"
)

SENDER_EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.\w+")


@dataclass(frozen=True)
class ParsedGmailMessage:
    gmail_message_id: str
    thread_id: str | None
    subject: str
    sender_email: str
    raw_snippet: str | None
    body_text: str
    received_at: datetime


class GmailClient:
    def __init__(
        self,
        credentials: Credentials,
        *,
        on_token_refresh: Callable[[Credentials], None] | None = None,
    ) -> None:
        self._credentials = credentials
        self._on_token_refresh = on_token_refresh
        self._service: Any | None = None

    def _ensure_service(self) -> Any:
        if self._credentials.expired and self._credentials.refresh_token:
            self._credentials.refresh(Request())
            if self._on_token_refresh is not None:
                self._on_token_refresh(self._credentials)

        if self._service is None:
            self._service = build(
                "gmail",
                "v1",
                credentials=self._credentials,
                cache_discovery=False,
            )
        return self._service

    def list_message_ids(self, query: str, max_results: int) -> list[str]:
        service = self._ensure_service()
        response = (
            service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
        )
        messages = response.get("messages", [])
        return [message["id"] for message in messages]

    def get_message(self, message_id: str) -> dict[str, Any]:
        service = self._ensure_service()
        return service.users().messages().get(userId="me", id=message_id, format="full").execute()

    def fetch_recent_messages(
        self,
        *,
        query: str = DEFAULT_JOB_SEARCH_QUERY,
        max_results: int = 50,
    ) -> list[ParsedGmailMessage]:
        message_ids = self.list_message_ids(query=query, max_results=max_results)
        return [self.parse_message(self.get_message(message_id)) for message_id in message_ids]

    async def fetch_recent_messages_async(
        self,
        *,
        query: str = DEFAULT_JOB_SEARCH_QUERY,
        max_results: int = 50,
    ) -> list[ParsedGmailMessage]:
        return await asyncio.to_thread(
            self.fetch_recent_messages,
            query=query,
            max_results=max_results,
        )

    @classmethod
    def parse_message(cls, raw: dict[str, Any]) -> ParsedGmailMessage:
        headers = {
            header["name"].lower(): header["value"]
            for header in raw.get("payload", {}).get("headers", [])
        }
        snippet = raw.get("snippet", "")
        body_text = cls._extract_body(raw.get("payload", {})) or snippet
        received_at = cls._parse_received_at(raw, headers)

        return ParsedGmailMessage(
            gmail_message_id=raw["id"],
            thread_id=raw.get("threadId"),
            subject=headers.get("subject", "(no subject)"),
            sender_email=cls._parse_sender(headers.get("from", "")),
            raw_snippet=snippet,
            body_text=body_text,
            received_at=received_at,
        )

    @staticmethod
    def _parse_sender(from_header: str) -> str:
        match = SENDER_EMAIL_RE.search(from_header)
        return match.group(0) if match else from_header.strip()

    @staticmethod
    def _parse_received_at(raw: dict[str, Any], headers: dict[str, str]) -> datetime:
        internal_date = raw.get("internalDate")
        if internal_date is not None:
            return datetime.fromtimestamp(int(internal_date) / 1000, tz=UTC)

        date_header = headers.get("date")
        if date_header:
            parsed = email.utils.parsedate_to_datetime(date_header)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=UTC)
            return parsed.astimezone(UTC)

        return datetime.now(UTC)

    @classmethod
    def _extract_body(cls, payload: dict[str, Any]) -> str:
        body_data = payload.get("body", {}).get("data")
        if body_data:
            return cls._decode_body_data(body_data)

        for part in payload.get("parts", []):
            mime_type = part.get("mimeType", "")
            if mime_type == "text/plain":
                part_data = part.get("body", {}).get("data")
                if part_data:
                    return cls._decode_body_data(part_data)

        for part in payload.get("parts", []):
            nested = cls._extract_body(part)
            if nested:
                return nested

        return ""

    @staticmethod
    def _decode_body_data(data: str) -> str:
        padded = data + "=" * (-len(data) % 4)
        return base64.urlsafe_b64decode(padded).decode("utf-8", errors="replace")
