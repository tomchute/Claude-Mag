"""Small shared helpers: issue ids, URLs, HTTP, word counts."""

from __future__ import annotations

import datetime as dt
import re
import time
import urllib.request
from urllib.parse import urlsplit, urlunsplit

USER_AGENT = "Mozilla/5.0 (compatible; claude-mag/0.1; personal reading digest)"


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


def normalize_url(url: str | None) -> str | None:
    """Strip query/fragment and trailing slash so the same post dedupes across RSS and email."""
    if not url:
        return None
    parts = urlsplit(url.strip())
    host = parts.netloc.lower().removeprefix("www.")
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower() or "https", host, path, "", ""))


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
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read(), resp.headers.get("Content-Type", "")
        except Exception as exc:  # noqa: BLE001 — network errors come in many shapes
            last = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"GET {url} failed: {last}")
