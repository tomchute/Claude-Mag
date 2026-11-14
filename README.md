# Claude Mag

A personal weekly magazine for your Kindle. Every Monday, GitHub Actions collects
new articles from the websites and newsletters you choose. Claude reads the list
against a short description of your tastes, suggests a shortlist, and asks which
pieces you want. Once you choose, Actions builds an EPUB with a cover and a table
of contents, and emails it to your Kindle.

```
Mon 04:17 UTC  gather.yml       RSS feeds + newsletter emails  ->  issues/<week>/candidates.json (titles, links, short summaries)
Mon morning    Claude (/mag)    reads candidates + interests.md, sends you a shortlist and asks which you want
You choose     multiple choice  Claude commits issues/<week>/picks.yaml to main
On that push   build-send.yml   fetch full text -> EPUB -> validate -> email to Kindle -> record in history.json
```

Full article text exists only on the GitHub Actions machine while the issue is
built, and in a private workflow artifact that is deleted after 14 days. Only
titles, links and a summary of up to 60 words are saved to the repository.

## What you need

- A **GitHub** account. A private repository is fine; this uses a few minutes of
  free Actions time a week.
- A **Gmail** account with 2-Step Verification turned on. It sends the EPUB to your
  Kindle, and can also collect email newsletters. You can make a separate Gmail
  account for this.
- A **Kindle** (or the Kindle app) and access to your Amazon account settings.
- **Claude Code** with access to your GitHub repository, for example on the web at
  [claude.ai/code](https://claude.ai/code). This is optional: you can also make your
  picks by hand (see [Picking without Claude](#picking-without-claude)).

## First-time setup

### 1. Make your own copy

Copy this repository into your own GitHub account. Use *Use this template* if it's
offered, otherwise fork it or push a clone to a new private repository.
Then open the **Actions** tab and turn workflows on if GitHub asks. Forks start
with scheduled workflows switched off.

### 2. Clear out the previous owner's data

The copy you start from may contain someone else's issues and reading history.
Reset them:

- Delete everything inside `issues/`.
- Replace `history.json` with:
  ```json
  { "sent": [] }
  ```
  This file records what has been sent, so the same article is never sent twice.
- Rewrite `interests.md` for yourself (see [step 7](#7-describe-your-tastes)).
- Replace the previous owner's name with yours wherever it appears:
  - `.claude/skills/mag/SKILL.md`, which tells Claude how to run each week and greets you by name
  - `CLAUDE.md`
  - `cover_subtitle` in `sources.yaml`, the line printed on the cover

  To find every place, search the repository for the old name.

### 3. Create a Gmail app password

Your normal Gmail password won't work here. Make a separate app password:

1. Turn on 2-Step Verification for the Google account if it isn't on already.
2. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords),
   create a password called "Claude Mag", and copy the 16 characters it shows you.
3. In Gmail, go to **Settings → See all settings → Forwarding and POP/IMAP** and
   make sure **IMAP** is enabled. Gather needs it to read newsletters.

### 4. Allow your Gmail address to send to your Kindle

1. On Amazon, go to **Manage Your Content and Devices → Preferences → Personal
   Document Settings**.
2. Copy your Kindle's **Send-to-Kindle email address** (it ends in `@kindle.com`).
3. On the same page, add your Gmail address to the **Approved Personal Document
   E-mail List**. Without this, Amazon silently ignores the emails.

### 5. Add the secrets to GitHub

In your repository, go to **Settings → Secrets and variables → Actions → New
repository secret** and add:

| Secret | Value |
|---|---|
| `GMAIL_USER` | your Gmail address |
| `GMAIL_APP_PASSWORD` | the 16-character app password from step 3 |
| `KINDLE_EMAIL` | your `…@kindle.com` address from step 4 |

These are only used inside GitHub Actions. They never appear in the repository.

### 6. Choose your sources

Edit `sources.yaml`. See [Adding and changing sources](#adding-and-changing-sources).
The feeds already listed are fine to start with.

### 7. Describe your tastes

`interests.md` is the brief Claude edits to. Write it in plain language. Claude
looks for these headings, so keep them:

- **Ongoing threads**: questions you're currently thinking through, and what would
  help. Claude favours articles that move one of these forward.
- **Topics I love**: subjects you always want to hear about.
- **Writers and publications I trust**: one line per source, with any caveats
  (e.g. "good on research, skip the opinion pieces").
- **Less of this**: what to leave out, such as hype, a particular outlet or a genre.
- **Recent signals**: leave this empty. Claude adds a few notes each week about what
  you picked and skipped, so its suggestions improve over time.

You can also add standing rules, such as "always star posts from X". Claude follows them.

### 8. Test it

1. Go to **Actions → gather → Run workflow**. Leave the boxes empty, or enter
   `30` in *lookback* to collect a month of articles the first time.
2. When it finishes, check that `issues/<this week>/candidates.json` was committed
   and has articles in it. Feeds that failed are listed under `errors` at the top
   of the file and in the run's summary.
3. Run the weekly flow once (step 9), or make picks by hand, and check that the
   issue reaches your Kindle. Allow a few minutes.

### 9. Set up the weekly Claude run

Open a Claude Code session on your repository and type `/mag`. Claude will:

1. check the candidates are fresh (and re-run gather if not),
2. show you a shortlist grouped by section, with the strongest picks marked ★,
3. ask which you want, as multiple-choice questions,
4. commit your picks, watch the build, and tell you whether it reached your Kindle.

To get this every Monday, ask Claude in that session to *"schedule a weekly task
every Monday at 8am my time that runs /mag"*. Pick a time after gather, which
runs at 04:17 UTC.

## Adding and changing sources

Everything about where articles come from lives in `sources.yaml`.

### Website feeds (RSS or Atom)

Feeds are grouped into **sections**, which become the sections of your magazine:

```yaml
sections:
  - id: science                 # short name, no spaces; used internally
    title: Science & Nature      # shown in the magazine
    feeds:
      - name: Quanta Magazine    # shown as the source of each article
        url: https://www.quantamagazine.org/feed/
```

- **Add a feed:** add a `- name:` / `url:` pair under the section you want.
- **Remove a feed:** delete its two lines.
- **Add a section:** add a new block with its own `id`, `title` and `feeds`. Claude
  will include it in the shortlist automatically.
- **Rename a section:** change its `title`. Avoid changing `id` once issues have
  been made with it.

**Finding a site's feed URL.** Try the site's address followed by `/feed`,
`/rss`, `/feed.xml` or `/rss.xml`. You can also look for an RSS link in the footer,
or view the page source and search for `application/rss+xml`. A feed URL opens
as raw XML in your browser, not as a normal web page.

**If a feed doesn't work:** after the next gather, look at `errors` in that week's
`candidates.json`. A `403` means the site blocks automated readers. Respect that
and remove it, or follow it by email instead (see below). A `404` means the URL
is wrong.

Two settings near the top control how much is collected:

```yaml
lookback_days: 8   # how far back each Monday's gather looks
max_per_feed: 4    # at most this many newest articles from each feed
```

### Email newsletters (Substack and similar)

Many newsletters, including all `*.substack.com` ones, block automated feed
readers. Subscribe to them **by email** instead. This also gets you the full text
of posts you've paid for.

1. Subscribe with your Gmail address.
2. In Gmail, create a label called `claude-mag`.
3. Create a filter: **From** `substack.com` (add other senders with `OR`) → **Apply
   the label** `claude-mag`. Tick *Skip the Inbox* if you don't want them in your inbox.
   Tick *Also apply filter to matching conversations* to include emails you already have.

Each Monday, gather reads that label. The label name and destination section are
set in `sources.yaml`:

```yaml
gmail:
  label: claude-mag   # the Gmail label to read
  section: substack   # which section newsletters go to by default
  route:              # send particular newsletters to other sections
    erictopol: science   # any sender whose name or address contains "erictopol"
```

Welcome emails, receipts and other non-post emails are skipped automatically.

### Classic texts ("From the Shelf")

Each week Claude may also suggest a few public-domain pieces: poems, short stories,
essays or letters from Project Gutenberg or Wikisource. You can rename this section:

```yaml
classics:
  id: classics
  title: From the Shelf
```

### The look of each issue

```yaml
title_format: "Claude Mag · {year} · Wk {week:02d}"   # the title shown in your Kindle library
cover_subtitle: "My Weekly Picks"                     # the line under the masthead on the cover; blank for none
```

## Picking without Claude

You can make an issue by hand. After gather runs, open
`issues/<week>/candidates.json`, note the `id` of each article you want (`c01`,
`c02`, …), and commit a file `issues/<week>/picks.yaml` to `main`:

```yaml
note: |
  A short editor's note for the first page (optional).
picks:
  - id: c03
    note: Why it's here (optional, shown under the title).
  - id: c12
  - title: The Lady with the Dog            # a public-domain text not in the candidates
    author: Anton Chekhov
    year: "1899"
    url: https://www.gutenberg.org/cache/epub/<number>/pg<number>.txt
    start: "<exact first line of the piece>"   # optional: cut a piece out of a longer book
    end: "<exact last line of the piece>"
```

Pushing that file to `main` starts the build and sends the issue.

## Running things by hand

- **The whole weekly flow:** type `/mag` in a Claude Code session on the repository.
  If this week's issue has already been sent, it makes a bonus issue
  (`2026-W46-2`, shown as *Wk 46 (2)* on the Kindle).
- **Gather only:** **Actions → gather → Run workflow**. It won't overwrite a week
  that already has picks unless you tick *force*.
- **Rebuild or resend an issue:** **Actions → build-send → Run workflow** with the
  issue id (e.g. `2026-W46`). *dry_run* is on by default, which builds the EPUB as
  a downloadable artifact without emailing it.

## Kindle notes

- Issues appear as `Claude Mag · 2026 · Wk 46` in your library, so they sort
  together. Emailed documents can't be put into a Collection automatically, so add
  them to one on the device.
- Each issue has a generated cover, an "In this issue" page with the editor's
  note, and a table of contents grouped by section.
- If an issue doesn't arrive, check that your Gmail address is on Amazon's approved
  list (step 4), then look at the `build-send` run in the Actions tab.

## For developers

```
pip install -r requirements-dev.txt
python -m pytest -q                                              # includes epubcheck when Java is installed
python -m mag gather --out out/candidates.json                   # needs network access to the feeds
python -m mag build --candidates out/candidates.json --auto 2    # dry-run issue in out/
python -m epubcheck out/*.epub
```

The code is in `mag/`: `gather` (feeds and email), `fetch` (full text),
`sanitize`, `epub` (book and cover), `send` (email), and the command line in
`__main__.py`.
