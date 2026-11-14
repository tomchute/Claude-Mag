"""Read newsletter emails (e.g. paid Substack posts) from a Gmail label over IMAP.

Needs GMAIL_USER and GMAIL_APP_PASSWORD. Runs in GitHub Actions only — the
Claude cloud sandbox cannot open IMAP connections.
"""

from __future__ import annotations

import datetime as dt
import email
import email.utils
import imaplib
import re
from email import policy
from email.message import EmailMessage

from .sanitize import html_to_text
from .util import clean_url, count_words, first_words

IMAP_HOST = "imap.gmail.com"

# Substack (and similar) post URLs: https://<pub>.substack.com/p/<slug>, custom domains, open.substack.com/pub/<pub>/p/<slug>
POST_URL = re.compile(r"""https?://[^\s"'<>]+?/p/[A-Za-z0-9][A-Za-z0-9-]*""")
SKIP_URL = re.compile(r"/(comments|subscribe|app-link|redirect|action)(/|$)|/p/[^/]+/comments", re.I)


def _html_part(msg: EmailMessage) -> str:
    part = msg.get_body(preferencelist=("html",))
    if part is not None:
        return part.get_content()
    part = msg.get_body(preferencelist=("plain",))
    if part is not None:
        from html import escape

        return "".join(f"<p>{escape(p)}</p>" for p in part.get_content().split("\n\n") if p.strip())
    return ""


def find_post_url(html: str) -> str | None:
    for m in POST_URL.finditer(html):
        url = m.group(0)
        if SKIP_URL.search(url):
            continue
        return clean_url(url)
    return None


def parse_newsletter(msg: EmailMessage) -> dict:
    """Pull candidate metadata out of one newsletter email."""
    html = _html_part(msg)
    text = html_to_text(html)
    from_name, from_addr = email.utils.parseaddr(str(msg.get("From", "")))
    date = msg.get("Date")
    try:
        published = email.utils.parsedate_to_datetime(str(date)).astimezone(dt.timezone.utc).isoformat()
    except (TypeError, ValueError):
        published = None
    return {
        "origin": "email",
        "message_id": str(msg.get("Message-ID", "")).strip(),
        "title": str(msg.get("Subject", "")).strip(),
        "source": from_name or from_addr,
        "sender": f"{from_name} <{from_addr}>",
        "author": None,
        "url": find_post_url(html),
        "published": published,
        "summary": first_words(text, 60),
        "words": count_words(text),
    }


def message_html(msg: EmailMessage) -> str:
    return _html_part(msg)


class Gmail:
    def __init__(self, user: str, password: str, label: str):
        self.user, self.password, self.label = user, password, label
        self._imap: imaplib.IMAP4_SSL | None = None

    def __enter__(self) -> Gmail:
        self._imap = imaplib.IMAP4_SSL(IMAP_HOST)
        self._imap.login(self.user, self.password)
        typ, _ = self._imap.select(f'"{self.label}"', readonly=True)
        if typ != "OK":
            raise RuntimeError(f"Gmail label {self.label!r} not found — create it and a filter that applies it")
        return self

    def __exit__(self, *exc) -> None:
        if self._imap is not None:
            try:
                self._imap.logout()
            except Exception:  # noqa: BLE001
                pass

    def _fetch(self, num: bytes) -> EmailMessage:
        assert self._imap is not None
        typ, data = self._imap.fetch(num, "(BODY.PEEK[])")
        raw = next(part[1] for part in data if isinstance(part, tuple))
        return email.message_from_bytes(raw, policy=policy.default)  # type: ignore[return-value]

    def since(self, since: dt.date) -> list[EmailMessage]:
        assert self._imap is not None
        typ, data = self._imap.search(None, "SINCE", since.strftime("%d-%b-%Y"))
        return [self._fetch(n) for n in (data[0] or b"").split()]

    def by_message_id(self, message_id: str) -> EmailMessage | None:
        assert self._imap is not None
        typ, data = self._imap.search(None, "HEADER", "Message-ID", message_id)
        nums = (data[0] or b"").split()
        return self._fetch(nums[-1]) if nums else None
