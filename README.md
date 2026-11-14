# Claude Mag

A weekly magazine, edited by Claude and you, delivered to Kindle as an EPUB.

```
Mon 04:17 UTC  gather.yml      RSS feeds + Gmail label "claude-mag"  ->  issues/<week>/candidates.json (metadata only)
Mon morning    Claude session  reads candidates + interests.md, sends you a numbered shortlist
You reply      "1 3 5 11 14"   Claude commits issues/<week>/picks.yaml to main
on that push   build-send.yml  fetch full text -> EPUB -> epubcheck -> email to Kindle -> record in history.json
```

Article text only ever exists on the Actions runner and in a 14-day private
workflow artifact. It is never committed.

## One-time setup

1. **Repo secrets** (Settings → Secrets and variables → Actions):
   - `GMAIL_USER`: your Gmail address
   - `GMAIL_APP_PASSWORD`: a Google [app password](https://myaccount.google.com/apppasswords) (needs 2-step verification)
   - `KINDLE_EMAIL`: your `…@kindle.com` address (Amazon → Manage Your Content and Devices → Preferences → Personal Document Settings)
2. **Amazon:** in the same Personal Document Settings page, add your Gmail address to the *Approved Personal Document E-mail List*.
3. **Gmail:** create a label `claude-mag` and a filter that applies it to paid newsletters (e.g. `from:(@substack.com)`). Make sure IMAP is enabled in Gmail settings.
4. **Feeds:** edit `sources.yaml`.
5. **Interests:** replace `interests.md`.
6. **Weekly session:** a scheduled Claude task runs the `mag` skill (`.claude/skills/mag/SKILL.md`) each Monday after gather.

## Local use

```
pip install -r requirements-dev.txt
python -m pytest -q
python -m mag gather --out out/candidates.json                 # needs network access to the feeds
python -m mag build --candidates out/candidates.json --auto 2   # dry-run issue in out/
python -m epubcheck out/*.epub
```

Manual runs: Actions → `build-send` → *Run workflow* with an issue id. `dry_run` is on by default.

## Kindle notes
- Issues appear as `Claude Mag · 2026 · Wk 46` in your library, so they sort together. Emailed documents can't be put into a Collection automatically, so add them to one on the device.
- The EPUB has a generated cover, an "In this issue" page with the editor's note, and a table of contents grouped by section.
