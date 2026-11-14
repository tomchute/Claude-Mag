# CLAUDE.md: claude-mag

A weekly personal magazine. GitHub Actions fetch and build; Claude curates and talks to Tom. See `README.md` for the flow.

- **Weekly run:** follow `.claude/skills/mag/SKILL.md`.
- **Layout:** `mag/` (Python package: gather, fetch, sanitize, epub, send, CLI in `__main__.py`), `sources.yaml` (feeds), `interests.md` (taste), `issues/<YYYY-Www>/` (candidates.json from gather, picks.yaml from Claude, sent.json from build-send), `history.json` (everything sent, used for dedupe).
- **Network:** the Claude cloud sandbox cannot reach feeds, publishers, Gmail IMAP or SMTP. Anything that fetches or sends runs in Actions. Test locally with fixtures (`tests/fixtures`).
- **Rights:** never commit article text or EPUBs. Candidates carry at most a ~60-word summary.
- **Before pushing code:** `python -m pytest -q` (includes epubcheck when Java is present).
- **Branches:** code changes go on a branch and merge to `main`. The weekly run commits `picks.yaml` and `interests.md` straight to `main`, because that push is what triggers the build.
- **Commits:** `<area>: <imperative summary>`, e.g. `epub: add section dividers`, `issue: 2026-W46 picks (6 pieces)`.
