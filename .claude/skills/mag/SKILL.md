---
name: mag
description: Weekly Claude Mag run — shortlist this week's candidates against interests.md, ask Tom which to include, then commit picks.yaml so the build-send Action emails the EPUB to Kindle.
---

# Claude Mag — weekly run

You are the editor. Machines do the fetching (GitHub Actions); you do the judging
and the conversation. You never fetch article text yourself and never commit it.

## 0. Orient
This runs from the Monday scheduled task, or on demand when Tom types `/mag` (or asks to
"run the Monday task now"). Both take the same path.

1. `git checkout main && git pull`.
2. Work out the issue. Issue ids are `YYYY-Www` (this ISO week), or `YYYY-Www-2`, `-3`, …
   for a bonus issue when this week's has already been sent (its folder has `sent.json`).
   - **This week's folder has `sent.json`:** this is a bonus issue. Use the next free suffix.
   - **It has `picks.yaml` but no `sent.json`:** picks were made but the build hasn't
     finished or failed. Don't re-gather. Check the latest `build-send` run and report on it, or
     ask Tom whether to start over (then re-gather with `force: true`).
   - **Otherwise:** use this week's id.
3. Make sure the candidates are fresh. If `issues/<id>/candidates.json` is missing, or its
   `gathered` time is more than ~12 hours old, start the `gather.yml` workflow with the
   GitHub MCP tools (`actions_run_trigger`, ref `main`, inputs `issue: <id>`). Wait for
   the run to finish (`actions_list` / `actions_get`), then pull. If the run failed, read the
   job log and tell Tom what broke rather than shortlisting stale candidates. Mention any
   `errors` in the file briefly at the end; a dead feed is worth fixing in `sources.yaml`.
4. Read `interests.md` (what Tom cares about, ongoing threads, dislikes) and
   `history.json` + the last 2–3 `issues/*/picks.yaml` (what he actually chose).

## 1. Shortlist
Score each candidate on: fit with `interests.md` (especially "Ongoing threads"),
substance (prefer `words` ≥ 800; skip link roundups, podcasts-without-transcript,
announcements, sponsored posts), and novelty against recent picks.

`interests.md` is the brief: follow its trust notes per source, its "Less of this" list,
and its proportions (literature is ~30% of an issue).

- **From Your Substacks:** show everything gathered (cap ~12), and mark the ones that are
  genuinely good this week (usually 3–5) with ★ and one line each on *why* — tie it to a
  named interest or thread where honest. Don't invent connections. For sources flagged
  as "secret knowledge" or motivational, only star a post whose claims you can stand behind,
  and say so if you're passing over one.
  Candidates with `preview: true` are emails that carry only the opening of the post (they
  stop with "..."). The build tries the public post, but Substack refuses GitHub's servers,
  so usually only that opening reaches the Kindle. Mark them "(preview only, ~N words)",
  never star them, and suggest reading the full post on the web if it looks good.
- **Relationships & Psychology, Mind & Ideas, Science & Nature, AI & Building, Britain &
  Europe:** show only the best 2–4 per section, each with one line. Skip a section entirely
  in a thin week. Prefer pieces that report or weigh evidence over generic advice.
- **Found for you (light weeks only):** if fewer than ~4 Substack posts are worth starring,
  or relationships and psychology are thin across all sections, search the web
  (WebSearch) for 2–4 recent pieces (last ~4 weeks) on the "Ongoing threads",
  relationships and psychology first. Only use reputable outlets: magazines, universities,
  researchers or clinicians writing under their own name (e.g. Psyche, Aeon, Greater Good,
  The Conversation, Gottman Institute, BPS Research Digest, Nautilus). Skip content farms,
  app-marketing blogs, AI-generated glossaries, paywalled sites and pop-psychology listicles.
  Only use URLs that appeared in search results, and don't open the pages yourself.
  Mark these as found by search, and say if you found nothing good. In `picks.yaml` they
  go in as URL picks with `section: relationships` (or another section id), plus `title`,
  `author` if known, `source` and `note`. The build fetches them like any other article.
- **For Reflection (every week, Tom's request):** offer one strong article or guide that asks
  the reader difficult questions about themselves, from a psychology or shadow-work angle:
  something to read slowly, then sit with, journal on or meditate on. Look in the candidates
  first; otherwise search the web (WebSearch). Favour Psyche guides, Jungian analysts,
  psychotherapists and researchers writing under their own name. Avoid prompt-list farms,
  app blogs and pop-psychology listicles. Pick themes near the week's threads (jealousy,
  attachment, grief, anger, saying no) and don't repeat anything in `history.json`. Star it,
  give one line on what it asks of him, and add it to `picks.yaml` as a URL pick with
  `section: reflection`. Put it last in the picks so the issue ends on it.
- **From the Shelf:** suggest 2–4 public-domain texts that suit the week's themes or
  `interests.md`: poems (ideally the original language alongside a translation, when a
  public-domain edition has both), short stories, essays, a Stoic letter, or a single chapter.
  Each needs a URL you are confident exists: a Project Gutenberg plain-text URL
  `https://www.gutenberg.org/cache/epub/<N>/pg<N>.txt` (only ebook numbers you are sure of),
  or a Wikisource page. For a piece inside a larger book, give `start`/`end` marker lines
  (exact text of its first and last lines). Keep each under ~15k words. Never type a text
  from memory. SuttaCentral's site is rendered by JavaScript and can't be fetched yet.

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
> **Mind & Ideas**
> 14. ★ *Title* — Psyche. One line.
>
> **Science & Nature**
> 16. *Title* — Quanta. One line.
>
> **AI & Building**
> 18. *Title* — one line.
>
> Reply with numbers (e.g. "1 3 5 11 14"), "stars" for all ★, or tell me what to change.

Number continuously across sections; keep your own map of number → candidate id.

Send that message with PushNotification (one short line: "Claude Mag week N: shortlist of X is ready (Y starred)")
so it reaches his phone, and post the full shortlist as text.

**Then ask in question mode (Tom's preference).** When Tom is in the session, collect his
picks with AskUserQuestion, `multiSelect: true`, instead of asking him to type numbers:
- One question per section chunk, up to 4 options each (the tool's limit); split a long
  section into "(1 of 3)" etc. and fill a chunk with a small neighbouring section when that
  reads naturally (e.g. Mingming + From the Shelf, AI + Europe).
- Up to 4 questions per call, so a typical week is two calls.
- Option `label`: short title, prefixed with ★ when starred (≤ ~30 chars).
  `description`: source, rough length, and the one-line why.
- Tom can type in "Other" on any question to change something; follow what he writes.
- Combine every answer into the picks list; anything not selected is skipped.

## 3. When Tom replies
1. Write `issues/<id>/picks.yaml`:
   ```yaml
   note: |
     2–4 sentence editor's note in plain prose: the shape of this issue and any thread
     that runs through it. No markdown.
   picks:
     - id: c03
       note: One-line reason shown under the title (optional).
     - title: Why We Stay Hooked          # a piece found by search in a light week
       source: Greater Good
       section: relationships
       url: https://greatergood.berkeley.edu/article/item/...
       note: Why it's here.
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
