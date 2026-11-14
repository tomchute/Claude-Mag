"""Resolve picks into full article bodies (sanitized XHTML)."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

import feedparser
import trafilatura

from .config import Config
from .gather import entry_html
from .sanitize import clean_html, html_to_text, slice_blocks, text_to_html
from .util import count_words, http_get, normalize_url

FULL_ENOUGH = 400  # words; feed content shorter than this is probably a teaser
PAYWALL_HINT = re.compile(r"(keep reading with a \d+-day free trial|this post is for paid subscribers|subscribe to keep reading)", re.I)


@dataclass
class Article:
    section: str
    title: str
    author: str | None
    source: str | None
    url: str | None
    published: str | None
    body: str  # sanitized XHTML fragment
    blurb: str | None = None

    @property
    def words(self) -> int:
        return count_words(html_to_text(self.body))


def extract_web(html: str) -> str:
    out = trafilatura.extract(
        html,
        output_format="html",
        include_comments=False,
        include_tables=False,
        include_images=False,
        include_links=True,
        include_formatting=True,
        favor_recall=True,
    )
    return clean_html(out or "")


def _first_heading_matches(body: str, title: str) -> bool:
    m = re.match(r"\s*<h2>(.*?)</h2>", body, re.S)
    return bool(m) and " ".join(html_to_text(m.group(1)).split()).lower() == " ".join(title.split()).lower()


def strip_duplicate_title(body: str, title: str) -> str:
    if _first_heading_matches(body, title):
        return re.sub(r"^\s*<h2>.*?</h2>\s*", "", body, count=1, flags=re.S)
    return body


class Fetcher:
    def __init__(self, cfg: Config, log=print):
        self.cfg = cfg
        self.log = log
        self._feeds: dict[str, feedparser.FeedParserDict] = {}
        self._gmail = None

    # -- sources ---------------------------------------------------------
    def _feed_for(self, cand: dict):
        section = self.cfg.section(cand["section"])
        for feed in section.feeds:
            if feed.name == cand.get("source"):
                if feed.url not in self._feeds:
                    raw, _ = http_get(feed.url)
                    self._feeds[feed.url] = feedparser.parse(raw)
                return self._feeds[feed.url]
        return None

    def _gmail_conn(self):
        if self._gmail is None:
            from .gmail import Gmail

            user, password = os.environ.get("GMAIL_USER"), os.environ.get("GMAIL_APP_PASSWORD")
            if not (user and password and self.cfg.gmail_label):
                raise RuntimeError("email pick needs GMAIL_USER, GMAIL_APP_PASSWORD and gmail.label")
            self._gmail = Gmail(user, password, self.cfg.gmail_label).__enter__()
        return self._gmail

    def close(self) -> None:
        if self._gmail is not None:
            self._gmail.__exit__(None, None, None)

    # -- resolution ------------------------------------------------------
    def from_rss(self, cand: dict) -> str:
        feed_body = ""
        feed = self._feed_for(cand)
        if feed is not None:
            for entry in feed.entries:
                if normalize_url(entry.get("link")) == cand["url"]:
                    feed_body = clean_html(entry_html(entry))
                    break
        text = html_to_text(feed_body)
        if count_words(text) >= FULL_ENOUGH and not PAYWALL_HINT.search(text):
            return feed_body
        try:
            raw, _ = http_get(cand["url"])
            web_body = extract_web(raw.decode("utf-8", "replace"))
        except Exception as exc:  # noqa: BLE001
            self.log(f"    web fetch failed, using feed text: {exc}")
            web_body = ""
        return max((feed_body, web_body), key=lambda b: count_words(html_to_text(b)))

    def from_email(self, cand: dict) -> str:
        from .gmail import message_html

        msg = self._gmail_conn().by_message_id(cand["message_id"])
        if msg is None:
            raise RuntimeError(f"email {cand['message_id']} no longer in label")
        html = message_html(msg)
        extracted = extract_web(html)
        whole = clean_html(html)
        # trafilatura is good at dropping newsletter chrome but can over-trim; fall back if it lost most of the text.
        if count_words(html_to_text(extracted)) >= 0.6 * count_words(html_to_text(whole)):
            return extracted
        return whole

    def candidate(self, cand: dict, blurb: str | None) -> Article:
        body = self.from_email(cand) if cand["origin"] == "email" else self.from_rss(cand)
        body = strip_duplicate_title(body, cand["title"])
        if count_words(html_to_text(body)) < 80:
            raise RuntimeError("extracted text is too short (paywall or extraction failure)")
        return Article(
            section=cand["section"],
            title=cand["title"],
            author=cand.get("author"),
            source=cand.get("source"),
            url=cand.get("url"),
            published=cand.get("published"),
            body=body,
            blurb=blurb,
        )

    def classic(self, pick: dict) -> Article:
        raw, ctype = http_get(pick["url"])
        if "text/plain" in ctype or pick["url"].endswith(".txt"):
            body = text_to_html(strip_gutenberg(raw.decode("utf-8", "replace")))
        else:
            body = extract_web(raw.decode("utf-8", "replace"))
        body = slice_blocks(body, pick.get("start"), pick.get("end"))
        body = strip_duplicate_title(body, pick["title"])
        return Article(
            section=pick.get("section", self.cfg.classics_section.id),
            title=pick["title"],
            author=pick.get("author"),
            source=pick.get("source"),
            url=pick["url"],
            published=pick.get("year"),
            body=body,
            blurb=pick.get("note"),
        )


def strip_gutenberg(text: str) -> str:
    start = re.search(r"\*\*\* ?START OF (THE|THIS) PROJECT GUTENBERG.*?\*\*\*", text, re.I)
    end = re.search(r"\*\*\* ?END OF (THE|THIS) PROJECT GUTENBERG", text, re.I)
    return text[start.end() if start else 0 : end.start() if end else len(text)]
