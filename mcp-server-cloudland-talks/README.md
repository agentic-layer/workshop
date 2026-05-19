# CloudLand 2026 Talks MCP Server

MCP server that exposes the [CloudLand 2026](https://my.doag.org/events/cloudland/2026/agenda/) agenda as tools for AI agents.

The server reads a **pre-scraped, committed JSON file** (`data/cloudland_2026.json.gz`); it never calls DOAG at runtime. To refresh the data, re-run the scraper.

The dataset is intentionally **PII-rich** (speaker names, employers, photos, LinkedIn / Twitter / Mastodon, personal websites and blogs) so the same MCP server can drive a PII-censoring demo in the workshop.

## Setup

```bash
uv sync --extra dev
```

## Run

```bash
uv run python server.py
```

Starts on `http://0.0.0.0:8000` with Streamable HTTP transport.

## Tools

| Tool | Purpose | Example query |
|---|---|---|
| `get_schedule_overview` | Conference dates, rooms, main-focus tracks, totals | "Overview of CloudLand 2026" |
| `get_talks_by_day(day)` | Sessions for an ISO date (`2026-05-20`) or day index (`1`–`4`) | "What's on Wednesday?" |
| `get_talks_by_room(room)` | Sessions in a room (substring match) | "What's in CloudLounge 1?" |
| `get_talks_by_focus(focus)` | Sessions in a Main Focus track | "Show me the AI & ML talks" |
| `get_talk_details(agenda_id)` | Full record with abstract, keywords, speakers | "Details on session 7122" |
| `search_talks(query)` | Substring search across title, abstract, keywords, speakers, room (with abstract previews) | "Find talks about Kubernetes" |
| `get_speaker_info(name)` | Bio, photo, social profiles, personal links, and a speaker's CloudLand sessions | "Who is Thomas Michael?" |

## MCP client configuration

```json
{
  "mcpServers": {
    "cloudland-talks": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

## Data refresh

`scrape.py` pulls the full dataset from `my.doag.org`. It is **resumable** and writes an auditable trail.

```bash
# full run (network + parse)
uv run python scrape.py

# only fetch missing items into the cache, do not rebuild JSON
uv run python scrape.py --net-only

# rebuild data/cloudland_2026.json.gz from cache only — no network
uv run python scrape.py --parse-only
```

Layout produced:

```
data/
├── cloudland_2026.json.gz          # committed product: parsed dataset (~75 KB gzipped, ~318 KB raw)
├── scrape.log                   # gitignored: one line per HTTP request
└── cache/                       # gitignored: raw responses
    ├── agenda.html
    ├── detail/<event_slot_id>.json
    └── speaker/<contributor_id>.json
```

**Resumability:** every request is cached on disk before parsing. On re-run, requests whose cache file already exists are skipped — the log marks them `method=CACHE status=hit`. Delete a cache file to force a refetch.

**Politeness:** all requests use User-Agent `felix.kampfer@qaware.de` with a 0.5 s delay between calls. First full run is ≈ 1 + 106 + 128 = 235 requests (~2 minutes). Subsequent runs make zero requests.

## What's in the JSON

```jsonc
{
  "conference": { "name": "CloudLand 2026", "start_date": "2026-05-19", ... },
  "days":   ["2026-05-19", "2026-05-20", "2026-05-21", "2026-05-22"],
  "rooms":  ["Aruba", "CloudLounge 1 Datev", ...],
  "talks": [
    {
      "agenda_id": "7122",
      "event_slot_id": "20022",
      "date": "2026-05-20", "start_time": "12:00", "end_time": "12:45",
      "title": "...", "room": "CloudLounge 1 Datev", "language_code": "de",
      "detail": {
        "abstract": "...", "keywords": ["Java", "Kubernetes", ...],
        "key_data": { "Main Focus": "DevOps", "Lecture Type": "...", ... },
        "speakers": [{"contributor_id": "13989", "name": "...", "company": "...", "photo_url": "..."}]
      }
    }
  ],
  "speakers": {
    "13989": {
      "name": "...", "company": "...", "board_position": "...",
      "photo_url": "...", "bio": "...",
      "labelled_links": {"website": "...", "blog": "...", ...},
      "socials": {"linkedin": "...", "twitter": "...", "mastodon": "..."},
      "talk_ids": ["7122"]
    }
  }
}
```

## Configuration

| Env Variable | Default | Description |
|---|---|---|
| `CLOUDLAND_DATA_PATH` | `data/cloudland_2026.json.gz` | Override the dataset path |
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `8000` | Listen port |

## Development

```bash
uv run python -m pytest tests/ -v
```
