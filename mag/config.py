"""Load sources.yaml."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Feed:
    name: str
    url: str


@dataclass
class Section:
    id: str
    title: str
    feeds: list[Feed] = field(default_factory=list)


@dataclass
class Config:
    title_format: str
    lookback_days: int
    max_per_feed: int
    sections: list[Section]
    gmail_label: str | None
    gmail_section: str
    classics_section: Section

    def section(self, sid: str) -> Section:
        if sid == self.classics_section.id:
            return self.classics_section
        for s in self.sections:
            if s.id == sid:
                return s
        raise KeyError(f"unknown section {sid!r}")

    @property
    def all_sections(self) -> list[Section]:
        return [*self.sections, self.classics_section]


def load(path: Path | None = None) -> Config:
    data = yaml.safe_load((path or ROOT / "sources.yaml").read_text())
    sections = [
        Section(s["id"], s["title"], [Feed(f["name"], f["url"]) for f in s.get("feeds") or []])
        for s in data["sections"]
    ]
    gmail = data.get("gmail") or {}
    classics = data.get("classics") or {}
    return Config(
        title_format=data.get("title_format", "Claude Mag · {year} · Wk {week:02d}"),
        lookback_days=int(data.get("lookback_days", 8)),
        max_per_feed=int(data.get("max_per_feed", 6)),
        sections=sections,
        gmail_label=gmail.get("label"),
        gmail_section=gmail.get("section", sections[0].id if sections else "substack"),
        classics_section=Section(classics.get("id", "classics"), classics.get("title", "From the Shelf")),
    )
