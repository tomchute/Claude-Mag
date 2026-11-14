"""Small shared helpers: issue ids, URLs, HTTP, word counts."""

from __future__ import annotations

import datetime as dt
import re
import time
import urllib.request
from urllib.parse import urlsplit, urlunsplit

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/130.0 Safari/537.36"
)
TRACKING = re.compile(r"^(utm_|r$|ref$|ref_src$|source$|publication_id$|post_id$|isFreemail$|triedRedirect$)", re.I)


def issue_id(day: dt.date) -> str:
    """ISO week id, e.g. 2026-W46."""
    year, week, _ = day.isocalendar()
    return f"{year}-W{week:02d}"


def issue_monday(issue: str) -> dt.date:
    year, week = issue.split("-W")
    return dt.date.fromisocalendar(int(year), int(week), 1)


def issue_title(fmt: str, issue: str) -> str:
    year, week = issue.split("-W")
    return fmt.format(year=int(year), week=int(week))


def clean_url(url: str | None) -> str | None:
    """The fetchable URL: tracking params and fragment removed, host and path untouched."""
    if not url:
        return None
    parts = urlsplit(url.strip())
    query = "&".join(q for q in parts.query.split("&") if q and not TRACKING.match(q.split("=", 1)[0]))
    return urlunsplit((parts.scheme or "https", parts.netloc, parts.path, query, ""))


def url_key(url: str | None) -> str | None:
    """Dedupe key only — never fetch this (dropping www. or a trailing slash can 404)."""
    if not url:
        return None
    parts = urlsplit(url.strip())
    host = parts.netloc.lower().removeprefix("www.")
    return f"{host}{parts.path.rstrip('/')}"


_WORD = re.compile(r"\w+(?:['’]\w+)*")


def count_words(text: str) -> int:
    return len(_WORD.findall(text or ""))


def first_words(text: str, n: int = 60) -> str:
    words = (text or "").split()
    out = " ".join(words[:n])
    return out + ("…" if len(words) > n else "")


def reading_minutes(words: int, wpm: int = 230) -> int:
    return max(1, round(words / wpm))


def http_get(url: str, timeout: int = 30, retries: int = 2) -> tuple[bytes, str]:
    """GET a URL; returns (body, content-type). Retries transient failures."""
    last: Exception | None = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-GB,en;q=0.9",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read(), resp.headers.get("Content-Type", "")
        except Exception as exc:  # noqa: BLE001 — network errors come in many shapes
            last = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"GET {url} failed: {last}")
