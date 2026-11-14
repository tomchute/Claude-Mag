import datetime as dt
import email
import json
import shutil
import subprocess
import zipfile
from email import policy
from pathlib import Path

import pytest

from mag import config, fetch
from mag import __main__ as cli
from mag.epub import build
from mag.gather import merge, parse_feed
from mag.gmail import find_post_url, parse_newsletter
from mag.sanitize import clean_html, slice_blocks, text_to_html
from mag.util import clean_url, issue_id, issue_monday, issue_title, parse_issue, url_key

FIX = Path(__file__).parent / "fixtures"
NOW = dt.datetime(2026, 11, 14, tzinfo=dt.timezone.utc)


def load_email():
    return email.message_from_bytes((FIX / "newsletter.eml").read_bytes(), policy=policy.default)


# --- util --------------------------------------------------------------------

def test_issue_ids():
    assert issue_id(dt.date(2026, 11, 14)) == "2026-W46"
    assert issue_monday("2026-W46") == dt.date(2026, 11, 9)
    assert issue_title("Claude Mag · {year} · Wk {week:02d}", "2027-W03") == "Claude Mag · 2027 · Wk 03"
    assert issue_id(dt.date(2026, 11, 14), 2) == "2026-W46-2"
    assert issue_monday("2026-W46-2") == dt.date(2026, 11, 9)
    assert issue_title("Claude Mag · {year} · Wk {week:02d}", "2026-W46-2") == "Claude Mag · 2026 · Wk 46 (2)"
    with pytest.raises(ValueError):
        parse_issue("2026-46")


def test_urls():
    assert clean_url("https://www.Example.com/p/x/?utm_source=rss&id=3&r=abc#c") == "https://www.Example.com/p/x/?id=3"
    assert url_key("https://www.Example.com/p/x/?id=3") == url_key("https://example.com/p/x") == "example.com/p/x"


# --- sanitize ----------------------------------------------------------------

def test_clean_html_layout_and_chrome():
    out = clean_html(
        "<table><tr><td><h1>T</h1><div>one</div><div>two <b>b</b></div></td></tr></table>"
        "<div class='subscribe-widget'>Subscribe</div><img src=x><script>x</script><p></p>"
        "<p><a href='javascript:x'>j</a> <a href='https://ok' onclick='1'>ok</a></p>"
    )
    assert out == "<h2>T</h2>\n<p>one</p>\n<p>two <b>b</b></p>\n<p><a>j</a> <a href=\"https://ok\">ok</a></p>"


def test_clean_html_wraps_loose_text_keeping_spaces():
    assert clean_html("Loose <em>inline</em> text<p>para</p>") == "<p>Loose <em>inline</em> text</p>\n<p>para</p>"


def test_slice_blocks():
    frag = clean_html("<p>Intro</p><p>Chapter I begins</p><p>middle</p><p>THE END</p><p>Licence</p>")
    assert slice_blocks(frag, "chapter i", "the end") == "<p>Chapter I begins</p>\n<p>middle</p>\n<p>THE END</p>"
    with pytest.raises(ValueError):
        slice_blocks(frag, "nope", None)


def test_text_to_html_escapes():
    assert text_to_html("a < b\nstill a\n\nnext") == "<p>a &lt; b still a</p>\n<p>next</p>"


# --- gather ------------------------------------------------------------------

def test_parse_feed_filters_old_and_normalizes():
    items = parse_feed((FIX / "feed.xml").read_bytes(), "substack", "Example Stack", NOW - dt.timedelta(days=8), 10)
    assert [i["title"] for i in items] == ["The Gut Renews Itself", "Paid: Sleep and Memory"]
    assert items[0]["url"] == "https://example.substack.com/p/the-gut-renews-itself"  # utm_source stripped
    assert items[0]["author"] == "Jane Writer"
    assert items[0]["words"] > 400 and items[1]["words"] < 50


def test_parse_newsletter_email():
    item = parse_newsletter(load_email())
    assert item["title"] == "Paid: Sleep and Memory"
    assert item["source"] == "Example Stack"
    assert item["url"] == "https://example.substack.com/p/sleep-and-memory"
    assert item["message_id"] == "<abc123@substack.com>"
    assert item["words"] > 400


def test_find_post_url_skips_comment_and_redirect_links():
    html = '<a href="https://x.com/p/slug/comments">c</a><a href="https://x.com/p/slug?r=1">t</a>'
    assert find_post_url(html) == "https://x.com/p/slug"


def test_merge_matches_email_to_rss_by_title_when_urls_differ():
    rss = parse_feed((FIX / "feed.xml").read_bytes(), "substack", "Example Stack", NOW - dt.timedelta(days=8), 10)
    mail = {**parse_newsletter(load_email()), "section": "substack", "url": "https://open.substack.com/pub/example/p/sleep-and-memory"}
    out = merge(rss, [mail], set())
    assert sorted((c["title"], c["origin"]) for c in out) == [("Paid: Sleep and Memory", "email"), ("The Gut Renews Itself", "rss")]


def test_merge_prefers_email_and_drops_sent():
    rss = parse_feed((FIX / "feed.xml").read_bytes(), "substack", "Example Stack", NOW - dt.timedelta(days=8), 10)
    sci = [{**rss[0], "section": "science", "url": "https://q.org/a", "title": "Sci", "published": "2026-11-12T00:00:00+00:00"}]
    mail = {**parse_newsletter(load_email()), "section": "substack"}
    out = merge(rss + sci, [mail], sent_urls={"https://example.substack.com/p/the-gut-renews-itself"})
    assert [(c["id"], c["title"], c["origin"]) for c in out] == [
        ("c01", "Paid: Sleep and Memory", "email"),
        ("c02", "Sci", "rss"),
    ]
    assert out[0]["author"] == "Jane Writer"  # kept from the RSS copy


# --- picks -------------------------------------------------------------------

def test_resolve_picks_rejects_unknown_ids():
    cands = [{"id": "c01"}]
    jobs = cli.resolve_picks({"picks": [{"id": "c01", "note": "n"}, {"title": "T", "url": "https://u"}]}, cands)
    assert [j["kind"] for j in jobs] == ["candidate", "classic"]
    with pytest.raises(SystemExit):
        cli.resolve_picks({"picks": [{"id": "c99"}]}, cands)


def test_auto_picks_takes_n_per_section():
    cands = [{"id": f"c{i}", "section": s} for i, s in enumerate("aaabbc")]
    assert [p["id"] for p in cli.auto_picks(cands, 2)["picks"]] == ["c0", "c1", "c3", "c4", "c5"]


# --- fetch + build (offline) ------------------------------------------------------

@pytest.fixture
def offline(monkeypatch):
    feed = (FIX / "feed.xml").read_bytes()
    gutenberg = (
        "Header junk\n*** START OF THE PROJECT GUTENBERG EBOOK X ***\n\nTHE TALE\n\n"
        + "\n\n".join(f"Paragraph {i} of the tale, with several words in it." for i in range(40))
        + "\n\nTHE END\n\n*** END OF THE PROJECT GUTENBERG EBOOK X ***\nLicence"
    ).encode()

    def fake_get(url, **_):
        if url.endswith(".txt"):
            return gutenberg, "text/plain; charset=utf-8"
        if "feed" in url:
            return feed, "application/rss+xml"
        raise RuntimeError("offline")

    class FakeGmail:
        def by_message_id(self, mid):
            return load_email()

    monkeypatch.setattr(fetch, "http_get", fake_get)
    monkeypatch.setattr(fetch.Fetcher, "_gmail_conn", lambda self: FakeGmail())


def make_cfg():
    cfg = config.load()
    cfg.sections[0].feeds = [config.Feed("Example Stack", "https://example.substack.com/feed")]
    return cfg


def test_fetch_and_build_valid_epub(offline, tmp_path):
    cfg = make_cfg()
    rss = parse_feed((FIX / "feed.xml").read_bytes(), "substack", "Example Stack", NOW - dt.timedelta(days=8), 10)
    mail = {**parse_newsletter(load_email()), "section": "substack"}
    f = fetch.Fetcher(cfg, log=lambda *_: None)

    gut = f.candidate(rss[0], "Builds on the microbiome thread.")
    assert gut.words > 400
    assert "<h2>The Gut Renews Itself</h2>" not in gut.body  # duplicate title removed
    assert "Subscribe" not in gut.body and "<img" not in gut.body

    with pytest.raises(RuntimeError):  # teaser only, web fetch offline
        f.candidate(rss[1], None)

    sleep = f.candidate(mail, None)
    assert "consolidating memories" in sleep.body
    assert "Unsubscribe" not in sleep.body

    tale = f.classic({"title": "The Tale", "author": "A. Author", "url": "https://gutenberg.org/x.txt", "start": "THE TALE", "end": "THE END"})
    assert tale.body.startswith("<p>THE TALE</p>") and tale.body.endswith("<p>THE END</p>")

    out = build(cfg, "2026-W46", [tale, gut, sleep], tmp_path / "mag.epub", note="Morning Tom.\n\nThree pieces this week.")
    with zipfile.ZipFile(out) as z:
        names = z.namelist()
        assert z.read("mimetype") == b"application/epub+zip"
        contents = z.read("EPUB/contents.xhtml").decode()
    assert "EPUB/cover.png" in names
    # sections follow config order: substack before classics
    assert contents.index("The Gut Renews Itself") < contents.index("The Tale")
    assert "Morning Tom." in contents

    if shutil.which("java"):
        res = subprocess.run(["python", "-m", "epubcheck", str(out)], capture_output=True, text=True)
        assert res.returncode == 0, res.stdout + res.stderr


def test_cli_build_and_dry_send(offline, tmp_path, monkeypatch):
    issues = tmp_path / "issues"
    folder = issues / "2026-W46"
    folder.mkdir(parents=True)
    rss = parse_feed((FIX / "feed.xml").read_bytes(), "substack", "Example Stack", NOW - dt.timedelta(days=8), 10)
    (folder / "candidates.json").write_text(json.dumps({"candidates": merge(rss, [], set())}))
    (folder / "picks.yaml").write_text("note: Hello.\npicks:\n  - id: c02\n    note: why\n  - id: c01\n")
    monkeypatch.setattr(cli, "ISSUES", issues)
    cfg = make_cfg()
    monkeypatch.setattr(cli.config, "load", lambda path=None: cfg)
    cli.main(["build", "--issue", "2026-W46", "--out", str(tmp_path / "out")])
    report = json.loads((tmp_path / "out" / "build-report.json").read_text())
    assert [a["title"] for a in report["articles"]] == ["The Gut Renews Itself"]
    assert [f["title"] for f in report["failures"]] == ["Paid: Sleep and Memory"]
    cli.main(["send", "--issue", "2026-W46", "--epub", report["epub"], "--dry-run"])


def test_gather_picks_bonus_issue_and_guards_picks(tmp_path, monkeypatch):
    issues = tmp_path / "issues"
    monkeypatch.setattr(cli, "ISSUES", issues)
    today = dt.date(2026, 11, 14)
    assert cli.next_issue(today) == "2026-W46"
    (issues / "2026-W46").mkdir(parents=True)
    (issues / "2026-W46" / "sent.json").write_text("{}")
    assert cli.next_issue(today) == "2026-W46-2"

    # A week that already has picks is not re-gathered (ids would shift under the picks)
    (issues / "2026-W46" / "picks.yaml").write_text("picks: []\n")
    called = []
    monkeypatch.setattr("mag.gather.gather", lambda *a, **k: called.append(1) or ([], []))
    monkeypatch.setattr(cli.config, "load", lambda path=None: None)
    cli.main(["gather", "--issue", "2026-W46"])
    assert not called and not (issues / "2026-W46" / "candidates.json").exists()
    cli.main(["gather", "--issue", "2026-W46", "--force"])
    assert called and (issues / "2026-W46" / "candidates.json").exists()
