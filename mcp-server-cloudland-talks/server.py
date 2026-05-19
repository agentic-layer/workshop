"""CloudLand 2026 Talks MCP server.

Reads a static, pre-scraped JSON file (data/cloudland_2026.json.gz) and
exposes the agenda as MCP tools. There are no outbound HTTP requests at
runtime — to refresh the dataset, re-run scrape.py.
"""
from __future__ import annotations

import gzip
import json
import os
from pathlib import Path

from fastmcp import FastMCP

DATA_PATH = Path(os.environ.get(
    "CLOUDLAND_DATA_PATH",
    str(Path(__file__).parent / "data" / "cloudland_2026.json.gz"),
))
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8000"))

LANG_MAP = {"de": "German", "en": "English"}


class Dataset:
    """In-memory indexes over the scraped CloudLand JSON."""

    def __init__(self, raw: dict):
        self.raw = raw
        self.conference: dict = raw.get("conference", {})
        self.days: list[str] = raw.get("days", [])
        self.rooms: list[str] = raw.get("rooms", [])
        self.talks: list[dict] = raw.get("talks", [])
        self.speakers: dict[str, dict] = raw.get("speakers", {})

        self._by_agenda_id: dict[str, dict] = {t["agenda_id"]: t for t in self.talks}
        self._by_day: dict[str, list[dict]] = {d: [] for d in self.days}
        self._by_room: dict[str, list[dict]] = {}
        self._by_focus: dict[str, list[dict]] = {}
        self._day_index_map: dict[str, str] = {
            str(i + 1): d for i, d in enumerate(self.days)
        }

        for t in self.talks:
            self._by_day.setdefault(t["date"], []).append(t)
            if t.get("room"):
                self._by_room.setdefault(t["room"], []).append(t)
            focus = (t.get("detail") or {}).get("key_data", {}).get("Main Focus")
            if focus and focus.lower() != "no mainfocus":
                self._by_focus.setdefault(focus, []).append(t)
        for talks in self._by_day.values():
            talks.sort(key=lambda t: (t["start_time"], t["room"]))

    def day_to_date(self, day: str) -> str | None:
        if day in self._by_day:
            return day
        if day in self._day_index_map:
            return self._day_index_map[day]
        return None

    def talk(self, agenda_id: str) -> dict | None:
        return self._by_agenda_id.get(str(agenda_id))

    def talks_for_day(self, date: str) -> list[dict]:
        return self._by_day.get(date, [])

    def talks_for_room(self, query: str) -> list[dict]:
        q = query.lower()
        return [t for t in self.talks if q in (t.get("room") or "").lower()]

    def talks_for_focus(self, query: str) -> list[dict]:
        q = query.lower()
        out: list[dict] = []
        for focus, talks in self._by_focus.items():
            if q in focus.lower():
                out.extend(talks)
        return out

    @property
    def all_focuses(self) -> list[str]:
        return sorted(self._by_focus.keys())


def load_dataset(path: Path = DATA_PATH) -> Dataset:
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as f:
        raw = json.load(f)
    return Dataset(raw)


dataset = load_dataset()
mcp = FastMCP("CloudLand 2026 Talks")


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------

def _lang_label(t: dict) -> str:
    detail_lang = (t.get("detail") or {}).get("key_data", {}).get("Language")
    if detail_lang:
        return detail_lang
    code = t.get("language_code")
    if code:
        return LANG_MAP.get(code, code)
    return "-"


def _speaker_names(t: dict) -> str:
    detail = t.get("detail") or {}
    if detail.get("speakers"):
        return ", ".join(s["name"] for s in detail["speakers"] if s.get("name"))
    return t.get("speaker_string") or "-"


def format_talks_table(talks: list[dict]) -> str:
    if not talks:
        return "No sessions found."
    lines = [
        "| ID | Date | Time | Title | Room | Lang | Focus | Speakers |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for t in talks:
        focus = (t.get("detail") or {}).get("key_data", {}).get("Main Focus") or "-"
        time_range = f"{t['start_time']}-{t['end_time']}" if t.get("end_time") else t["start_time"]
        lines.append(
            f"| {t['agenda_id']} | {t['date']} | {time_range} | {t['title']} "
            f"| {t.get('room') or '-'} | {_lang_label(t)} | {focus} | {_speaker_names(t)} |"
        )
    return "\n".join(lines)


def format_talk_detail(t: dict) -> str:
    detail = t.get("detail") or {}
    key = detail.get("key_data", {})
    lines = [f"# {t['title']}", ""]
    lines.append(f"- **Agenda ID:** {t['agenda_id']}")
    if t.get("event_slot_id"):
        lines.append(f"- **Event Slot ID:** {t['event_slot_id']}")
    time_range = f"{t['start_time']}-{t['end_time']}" if t.get("end_time") else t["start_time"]
    lines.append(f"- **Date:** {t['date']}")
    lines.append(f"- **Time:** {time_range}")
    lines.append(f"- **Room:** {t.get('room') or '-'}")
    if detail.get("room_capacity"):
        lines.append(f"- **Room capacity:** {detail['room_capacity']}")
    lines.append(f"- **Language:** {_lang_label(t)}")
    for k in ("Main Focus", "Lecture Type", "Speaker-Level", "with Demo", "format"):
        if k in key:
            lines.append(f"- **{k}:** {key[k]}")
    if detail.get("keywords"):
        lines.append(f"- **Keywords:** {', '.join(detail['keywords'])}")
    lines.append("")

    if detail.get("abstract"):
        lines.append("## Abstract")
        lines.append("")
        lines.append(detail["abstract"])
        lines.append("")

    if detail.get("speakers"):
        lines.append("## Speakers")
        lines.append("")
        for s in detail["speakers"]:
            label = s.get("name") or "(unknown)"
            if s.get("company"):
                label += f" — {s['company']}"
            if s.get("contributor_id"):
                label += f" (speaker_id: {s['contributor_id']})"
            lines.append(f"- {label}")
    return "\n".join(lines)


def format_speaker_info(s: dict) -> str:
    lines = [f"# {s.get('name') or '(unknown)'}", ""]
    if s.get("company"):
        lines.append(f"- **Affiliation:** {s['company']}")
    if s.get("board_position"):
        lines.append(f"- **Role:** {s['board_position']}")
    if s.get("contributor_id"):
        lines.append(f"- **Speaker ID:** {s['contributor_id']}")
    if s.get("photo_url"):
        lines.append(f"- **Photo:** {s['photo_url']}")
    lines.append("")

    socials = s.get("socials") or {}
    if socials:
        lines.append("## Social profiles")
        for platform, url in socials.items():
            lines.append(f"- **{platform.capitalize()}:** {url}")
        lines.append("")

    labelled = s.get("labelled_links") or {}
    if labelled:
        lines.append("## Links")
        for label, val in labelled.items():
            lines.append(f"- **{label.capitalize()}:** {val}")
        lines.append("")

    if s.get("bio"):
        lines.append("## Bio")
        lines.append("")
        lines.append(s["bio"])
        lines.append("")

    if s.get("talk_ids"):
        lines.append("## Sessions at CloudLand 2026")
        lines.append("")
        for tid in s["talk_ids"]:
            talk = dataset.talk(tid)
            if talk:
                time_range = (
                    f"{talk['start_time']}-{talk['end_time']}" if talk.get("end_time")
                    else talk["start_time"]
                )
                lines.append(
                    f"- **{talk['title']}** — {talk['date']} {time_range}, "
                    f"{talk.get('room') or '-'} (agenda_id: {talk['agenda_id']})"
                )
            else:
                lines.append(f"- (agenda_id: {tid} — not in dataset)")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool(annotations={"readOnlyHint": True})
async def get_schedule_overview() -> str:
    """Overview of CloudLand 2026: dates, rooms, main focus areas, session counts."""
    conf = dataset.conference
    lines = [
        f"# {conf.get('name', 'CloudLand 2026')}",
        "",
        f"- **Venue:** {conf.get('venue', '-')}",
        f"- **Host:** {conf.get('host', '-')}",
        f"- **Dates:** {conf.get('start_date')} to {conf.get('end_date')}",
        f"- **Timezone:** {conf.get('timezone', '-')}",
        f"- **Source:** <{conf.get('url', '')}>",
        f"- **Sessions:** {len(dataset.talks)} across {len(dataset.days)} days",
        f"- **Speakers:** {len(dataset.speakers)}",
        f"- **Data scraped at:** {conf.get('scraped_at', '-')}",
        "",
        "## Days",
        "",
    ]
    for idx, date in enumerate(dataset.days, start=1):
        talks = dataset.talks_for_day(date)
        rooms_in_day = sorted({t["room"] for t in talks if t.get("room")})
        lines.append(f"### Day {idx} — {date} ({len(talks)} sessions)")
        lines.append(f"- **Rooms:** {', '.join(rooms_in_day) if rooms_in_day else '-'}")
        lines.append("")
    lines.append("## Main focus areas")
    lines.append("")
    for focus in dataset.all_focuses:
        lines.append(f"- {focus}")
    lines.append("")
    lines.append("## Rooms")
    lines.append("")
    for room in dataset.rooms:
        lines.append(f"- {room}")
    return "\n".join(lines)


@mcp.tool(annotations={"readOnlyHint": True})
async def get_talks_by_day(day: str) -> str:
    """Get all CloudLand 2026 sessions for a day. Accepts an ISO date like '2026-05-20' or a day index '1'-'4' (1=May 19)."""
    date = dataset.day_to_date(day)
    if date is None:
        return (
            f"No sessions found for day '{day}'. "
            f"Valid dates: {', '.join(dataset.days)} or indices 1-{len(dataset.days)}."
        )
    talks = dataset.talks_for_day(date)
    return f"## Sessions on {date}\n\n{format_talks_table(talks)}"


@mcp.tool(annotations={"readOnlyHint": True})
async def get_talks_by_room(room: str) -> str:
    """All sessions in a room/venue. Case-insensitive substring match (e.g. 'cloudlounge' matches 'CloudLounge 1 Datev')."""
    talks = dataset.talks_for_room(room)
    if not talks:
        return f"No sessions found in room '{room}'. Available rooms: {', '.join(dataset.rooms)}"
    talks_sorted = sorted(talks, key=lambda t: (t["date"], t["start_time"]))
    return f"## Sessions in rooms matching '{room}' ({len(talks_sorted)} matches)\n\n{format_talks_table(talks_sorted)}"


@mcp.tool(annotations={"readOnlyHint": True})
async def get_talks_by_focus(focus: str) -> str:
    """All sessions in a 'Main Focus' track (e.g. 'AI & ML', 'DevOps', 'Platform Engineering'). Substring match."""
    talks = dataset.talks_for_focus(focus)
    if not talks:
        return f"No sessions found for focus '{focus}'. Available focuses: {', '.join(dataset.all_focuses)}"
    talks_sorted = sorted(talks, key=lambda t: (t["date"], t["start_time"]))
    return f"## Sessions in focus matching '{focus}' ({len(talks_sorted)} matches)\n\n{format_talks_table(talks_sorted)}"


@mcp.tool(annotations={"readOnlyHint": True})
async def get_talk_details(agenda_id: str) -> str:
    """Full session details by agenda_id (e.g. '7122'). Includes abstract, keywords, speakers (with names, companies, IDs)."""
    talk = dataset.talk(agenda_id)
    if talk is None:
        return f"No session with agenda_id '{agenda_id}' found."
    return format_talk_detail(talk)


@mcp.tool(annotations={"readOnlyHint": True})
async def search_talks(query: str) -> str:
    """Search across title, abstract, keywords, speaker names, room. Case-insensitive substring match."""
    q = query.lower()
    results: list[dict] = []
    for talk in dataset.talks:
        detail = talk.get("detail") or {}
        speakers_text = " ".join(
            f"{s.get('name','')} {s.get('company','')}" for s in (detail.get("speakers") or [])
        )
        haystack = " ".join([
            talk.get("title", ""),
            talk.get("room") or "",
            talk.get("speaker_string") or "",
            detail.get("abstract", ""),
            " ".join(detail.get("keywords") or []),
            speakers_text,
        ]).lower()
        if q in haystack:
            results.append(talk)
    if not results:
        return f"No sessions found matching '{query}'."
    results.sort(key=lambda t: (t["date"], t["start_time"]))
    parts = [f"## Search results for '{query}' ({len(results)} matches)\n\n{format_talks_table(results)}"]
    # Include abstract previews to make agent chaining easier
    for t in results[:10]:
        abstract = (t.get("detail") or {}).get("abstract", "").strip()
        if abstract:
            preview = abstract[:400] + ("…" if len(abstract) > 400 else "")
            parts.append(f"\n### {t['agenda_id']} — {t['title']}\n**Abstract:** {preview}")
    return "\n".join(parts)


@mcp.tool(annotations={"readOnlyHint": True})
async def get_speaker_info(name: str) -> str:
    """Look up a speaker by name (case-insensitive substring). Returns affiliation, photo, social profiles, bio, and their CloudLand sessions."""
    q = name.lower()
    matches = [s for s in dataset.speakers.values() if q in (s.get("name") or "").lower()]
    if not matches:
        sample = ", ".join(sorted(s.get("name", "") for s in list(dataset.speakers.values())[:20]))
        return f"No speaker matching '{name}'. {len(dataset.speakers)} speakers in dataset. Sample: {sample}"
    matches.sort(key=lambda s: s.get("name") or "")
    return "\n\n---\n\n".join(format_speaker_info(s) for s in matches)


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host=HOST, port=PORT)
