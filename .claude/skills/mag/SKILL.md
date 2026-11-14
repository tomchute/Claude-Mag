---
name: mag
description: Weekly Claude Mag run — shortlist this week's candidates against interests.md, ask Tom which to include, then commit picks.yaml so the build-send Action emails the EPUB to Kindle.
---

# Claude Mag — weekly run

You are the editor. Machines do the fetching (GitHub Actions); you do the judging
and the conversation. You never fetch article text yourself and never commit it.

## 0. Orient
1. `git checkout main && git pull`.
2. Issue id = this ISO week (`python -c "import datetime as d;y,w,_=d.date.today().isocalendar();print(f'{y}-W{w:02d}')"`).
3. Read `issues/<id>/candidates.json`. If missing, the Monday `gather` workflow has not
   run or failed: trigger it with the GitHub MCP tools (`actions_run_trigger`,
   workflow `gather.yml`, ref `main`), wait for it, pull again. Mention any `errors`
   in the file to Tom briefly at the end (a dead feed is worth fixing in `sources.yaml`).
4. Read `interests.md` (what Tom cares about, ongoing threads, dislikes) and
   `history.json` + the last 2–3 `issues/*/picks.yaml` (what he actually chose).

## 1. Shortlist
Score each candidate on: fit with `interests.md` (especially "Ongoing threads"),
substance (prefer `words` ≥ 800; skip link roundups, podcasts-without-transcript,
announcements, sponsored posts), and novelty against recent picks.

- **Substacks:** show everything gathered (cap ~12), and mark the ones that are
  genuinely good this week (usually 3–5) with ★ and one line each on *why* — tie it to a
  named interest or thread where honest. Don't invent connections.
- **Science / Technology:** show only the best 2–4 per section, each with one line.
- **From the Shelf:** suggest 2–3 public-domain texts that suit the week's themes or
  `interests.md` — short stories, essays, poems, or a single chapter. Each needs a
  plain-text URL you are confident exists: prefer Project Gutenberg
  `https://www.gutenberg.org/cache/epub/<N>/pg<N>.txt`, using only ebook numbers you
  are sure of. For a story inside a collection, give `start`/`end` marker lines
  (exact text of the first and last lines of the piece). Keep each under ~15k words.
  Never type a text from memory.

## 2. Ask Tom
End your turn with one message in this shape (it reaches his phone as a notification):

> Morning Tom — Claude Mag, week 46.
>
> **From your Substacks** — 10 new this week; 5 are worth your time:
> 1. ★ *Title* — Source. Why, in one line (builds on the sleep thread from last week).
> 2. *Title* — Source.
> …
>
> **From the Shelf**
> 11. *The Lady with the Dog* — Chekhov (1899, ~8k words). Why.
> …
>
> **Science** (Quanta, Nautilus)
> 14. ★ *Title* — one line.
>
> **Technology**
> 17. *Title* — one line.
>
> Reply with numbers (e.g. "1 3 5 11 14"), "stars" for all ★, or tell me what to change.

Number continuously across sections; keep your own map of number → candidate id.

## 3. When Tom replies
1. Write `issues/<id>/picks.yaml`:
   ```yaml
   note: |
     2–4 sentence editor's note in plain prose: the shape of this issue and any thread
     that runs through it. No markdown.
   picks:
     - id: c03
       note: One-line reason shown under the title (optional).
     - title: The Lady with the Dog
       author: Anton Chekhov
       year: "1899"
       url: https://www.gutenberg.org/cache/epub/<N>/pg<N>.txt
       start: "<exact first line>"
       end: "<exact last line>"
       note: Why it's here.
   ```
   Order picks as you'd want them read; the build groups them by section.
2. Commit straight to `main`: `issue: <id> picks (<n> pieces)`, push. That push starts
   the `build-send` workflow.
3. Watch it with the GitHub MCP actions tools until it finishes. Report back in one or two
   lines: sent (with piece count), or which pieces were skipped and why (the run summary and
   `build-report.json` artifact list them). If a classic failed on a bad URL or marker, fix
   `picks.yaml` and re-dispatch `build-send.yml` with `issue=<id>` and `dry_run=false`.
4. Append 1–3 bullets to "Recent signals" in `interests.md` (what he picked or pointedly
   skipped, any comment he made), keep that list to the last ~20 bullets, commit
   `interests: signals from <id>`.

## Rules
- Never commit article text, excerpts beyond the gathered summaries, or EPUBs.
- If nothing is worth sending this week, say so and skip the issue — no filler.
- Keep the message scannable on a phone: titles in italics, one line each, no essays.
