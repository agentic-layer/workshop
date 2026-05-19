"""Resumable scraper for CloudLand 2026 agenda data on my.doag.org.

Design goals:
- **Every HTTP request is cached on disk** under data/cache/ before any parsing.
- **Every request is logged** to data/scrape.log with timestamp, URL, body keys,
  HTTP status, byte count, and the cache filename written.
- **Resumable**: when re-run, requests whose cache file already exists are
  skipped (no second hit to DOAG). Delete a cache file to force a refetch.
- **Two phases** — (1) network: populate cache; (2) parse: build the final
  JSON file from the cache only (no network). You can re-run phase 2 freely.

Run:
    python scrape.py              # both phases
    python scrape.py --parse-only # rebuild data/cloudland_2026.json from cache
    python scrape.py --net-only   # only fetch missing items, don't rebuild JSON
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

AGENDA_URL = "https://my.doag.org/events/cloudland/2026/agenda/"
AJAX_URL = "https://my.doag.org/events/cloudland/2026/agenda/ajax_basic_spacer"
ASSET_BASE = "https://my.doag.org"
USER_AGENT = "felix.kampfer@qaware.de"

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
DETAIL_DIR = CACHE_DIR / "detail"
SPEAKER_DIR = CACHE_DIR / "speaker"
LOG_PATH = DATA_DIR / "scrape.log"
AGENDA_CACHE = CACHE_DIR / "agenda.html"
OUT_PATH = DATA_DIR / "cloudland_2026.json.gz"

# CloudLand is in Europe/Berlin (CEST = UTC+2 in May).
BERLIN_OFFSET_HOURS = 2
SLEEP_BETWEEN_REQUESTS = 0.5  # polite delay between consecutive network calls

SOCIAL_ICONS = {
    "linkedin": "fa-linkedin",
    "twitter": "fa-twitter",
    "x-twitter": "fa-x-twitter",
    "github": "fa-github",
    "mastodon": "fa-mastodon",
    "youtube": "fa-youtube",
    "xing": "fa-xing",
    "facebook": "fa-facebook",
    "instagram": "fa-instagram",
    "bluesky": "fa-bluesky",
}


# ---------------------------------------------------------------------------
# Logging / cache helpers
# ---------------------------------------------------------------------------

def log_request(method: str, url: str, body: dict | None, status: int | str,
                bytes_written: int, cache_path: Path, note: str = "") -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()
    body_summary = ""
    if body:
        # Compact, readable summary — does not log secrets (there are none).
        body_summary = " ".join(f"{k}={v}" for k, v in body.items())
    rel_cache = cache_path.relative_to(BASE_DIR)
    line = (
        f"{ts} | {method} {url} | body=({body_summary}) | "
        f"status={status} | bytes={bytes_written} | cache={rel_cache}"
    )
    if note:
        line += f" | note={note}"
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line)


def write_text_cache(path: Path, text: str) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = text.encode("utf-8")
    path.write_bytes(data)
    return len(data)


def fetch_agenda(client: httpx.Client) -> str:
    if AGENDA_CACHE.exists():
        log_request("CACHE", AGENDA_URL, None, "hit", AGENDA_CACHE.stat().st_size,
                    AGENDA_CACHE, note="skip (cache exists)")
        return AGENDA_CACHE.read_text(encoding="utf-8")
    r = client.get(AGENDA_URL, timeout=30.0)
    n = write_text_cache(AGENDA_CACHE, r.text)
    log_request("GET", AGENDA_URL, None, r.status_code, n, AGENDA_CACHE)
    r.raise_for_status()
    time.sleep(SLEEP_BETWEEN_REQUESTS)
    return r.text


def fetch_detail(client: httpx.Client, *, event_slot_id: str, event_agenda_id: str,
                 date_agenda_ts: int | None) -> dict:
    out_path = DETAIL_DIR / f"{event_slot_id}.json"
    body = {
        "ajax": "loadContent",
        "data[shortClassName]": "custom_eventSlot",
        "data[view]": "detail",
        "data[eventSlotId]": event_slot_id,
        "data[eventAgendaId]": event_agenda_id,
        "data[spacerContentLoader]": "overlay",
    }
    if date_agenda_ts:
        body["data[dateAgenda]"] = str(date_agenda_ts)

    if out_path.exists():
        log_request("CACHE", AJAX_URL, body, "hit", out_path.stat().st_size,
                    out_path, note="skip (cache exists)")
        return json.loads(out_path.read_text(encoding="utf-8"))

    r = client.post(AJAX_URL, data=body, timeout=30.0)
    n = write_text_cache(out_path, r.text)
    log_request("POST", AJAX_URL, body, r.status_code, n, out_path)
    r.raise_for_status()
    payload = r.json()
    if payload.get("status") != 0:
        # Still cached — we keep the failure for inspection
        raise RuntimeError(f"detail status={payload.get('status')} msg={payload.get('message')}")
    time.sleep(SLEEP_BETWEEN_REQUESTS)
    return payload


def fetch_speaker(client: httpx.Client, contributor_id: str) -> dict:
    out_path = SPEAKER_DIR / f"{contributor_id}.json"
    body = {
        "ajax": "loadContent",
        "data[shortClassName]": "custom_eventContributor",
        "data[view]": "speakerDetail",
        "data[eventContributorId]": contributor_id,
        "data[spacerContentLoader]": "overlay",
    }
    if out_path.exists():
        log_request("CACHE", AJAX_URL, body, "hit", out_path.stat().st_size,
                    out_path, note="skip (cache exists)")
        return json.loads(out_path.read_text(encoding="utf-8"))

    r = client.post(AJAX_URL, data=body, timeout=30.0)
    n = write_text_cache(out_path, r.text)
    log_request("POST", AJAX_URL, body, r.status_code, n, out_path)
    r.raise_for_status()
    payload = r.json()
    if payload.get("status") != 0:
        raise RuntimeError(f"speaker status={payload.get('status')} msg={payload.get('message')}")
    time.sleep(SLEEP_BETWEEN_REQUESTS)
    return payload


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def clean(text: str | None) -> str:
    if text is None:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def abs_url(maybe_relative: str | None) -> str | None:
    if not maybe_relative:
        return None
    if maybe_relative.startswith("http://") or maybe_relative.startswith("https://"):
        return maybe_relative
    if maybe_relative.startswith("/"):
        return ASSET_BASE + maybe_relative
    return maybe_relative


def ts_to_date(unix_ts: int) -> str:
    dt = datetime.fromtimestamp(unix_ts, tz=timezone.utc) + timedelta(hours=BERLIN_OFFSET_HOURS)
    return dt.strftime("%Y-%m-%d")


def parse_agenda_index(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    seen: set[str] = set()
    out: list[dict] = []
    for article in soup.select("article[id]"):
        art_id = article.get("id", "")
        if not art_id.isdigit():
            continue
        date_str = ts_to_date(int(art_id))
        for teaser in article.select("div.agendaEventSlotTeaser"):
            agenda_id = teaser.get("data-agenda-id")
            if not agenda_id or agenda_id in seen:
                continue
            seen.add(agenda_id)
            link = teaser.select_one("a.eventSlotLink")
            event_slot_id = link.get("data-event-slot-id") if link else None
            date_agenda = link.get("data-date-agenda") if link else art_id
            title = clean(teaser.select_one("div.title").get_text() if teaser.select_one("div.title") else "")
            speaker_str = clean(teaser.select_one("div.speaker").get_text() if teaser.select_one("div.speaker") else "")
            room = clean(teaser.select_one("div.room").get_text() if teaser.select_one("div.room") else "")
            start = clean(teaser.select_one("div.beginTime").get_text() if teaser.select_one("div.beginTime") else "")
            end = clean(teaser.select_one("div.endTime").get_text() if teaser.select_one("div.endTime") else "")
            language_code = None
            flag_div = teaser.select_one("div.flags")
            if flag_div:
                for cls in flag_div.get("class", []):
                    if cls.startswith("flag-") and cls != "flags":
                        language_code = cls[len("flag-"):]
                        break
            out.append({
                "agenda_id": agenda_id,
                "event_slot_id": event_slot_id,
                "date": date_str,
                "date_agenda_ts": int(date_agenda) if date_agenda and date_agenda.isdigit() else None,
                "start_time": start,
                "end_time": end,
                "title": title,
                "speaker_string": speaker_str,
                "room": room,
                "language_code": language_code,
            })
    return out


def parse_detail_payload(payload: dict) -> dict:
    html = payload.get("htmlContent") or ""
    soup = BeautifulSoup(html, "html.parser")

    title_el = soup.select_one("h1.title .BasicText") or soup.select_one("h1.title")
    title = clean(title_el.get_text()) if title_el else ""

    capacity = None
    cap_el = soup.select_one(".roomCapacityWrapper .roomCapacity")
    if cap_el and cap_el.get_text().strip().isdigit():
        capacity = int(cap_el.get_text().strip())

    speakers = []
    for li in soup.select("li.speakersList"):
        a = li.select_one("a.speakerDetailLink")
        contributor_id = a.get("data-event-contributor-id") if a else None
        name_el = li.select_one(".name")
        company_el = li.select_one(".company")
        img = li.select_one("img")
        speakers.append({
            "contributor_id": contributor_id,
            "name": clean(name_el.get_text()) if name_el else "",
            "company": clean(company_el.get_text()) if company_el else "",
            "photo_url": abs_url(img.get("src")) if img else None,
        })

    key_data: dict[str, str] = {}
    for row in soup.select("table.keydataTable tr"):
        cells = row.select("td")
        if len(cells) >= 2:
            k = clean(cells[0].get_text()).rstrip(":")
            v = clean(cells[1].get_text())
            key_data[k] = v

    abstract = ""
    abstract_el = soup.select_one(".abstractWrapper .abstract")
    if abstract_el:
        for br in abstract_el.find_all("br"):
            br.replace_with("\n")
        abstract = abstract_el.get_text("\n")
        abstract = re.sub(r"[ \t]+\n", "\n", abstract)
        abstract = re.sub(r"\n{3,}", "\n\n", abstract).strip()

    keywords = []
    kw_el = soup.select_one(".keywordsWrapper .keywords")
    if kw_el:
        keywords = [k.strip() for k in clean(kw_el.get_text()).split(",") if k.strip()]

    return {
        "title": title,
        "room_capacity": capacity,
        "speakers": speakers,
        "key_data": key_data,
        "abstract": abstract,
        "keywords": keywords,
    }


def parse_speaker_payload(payload: dict) -> dict:
    html = payload.get("htmlContent") or ""
    soup = BeautifulSoup(html, "html.parser")
    detail = soup.select_one(".CustomEventContributor.speakerDetail")
    if not detail:
        return {}

    name = clean(detail.select_one("h1").get_text()) if detail.select_one("h1") else ""
    company = clean(detail.select_one("p.company").get_text()) if detail.select_one("p.company") else ""
    board_position = clean(detail.select_one(".boardPosition").get_text()) if detail.select_one(".boardPosition") else ""
    img = detail.select_one(".leftWrapper img") or detail.select_one(".graphic img")
    photo = abs_url(img.get("src")) if img else None

    bio_parts: list[str] = []
    right = detail.select_one(".rightWrapper")
    if right:
        for el in right.find_all(["p", "div"], recursive=False):
            txt = clean(el.get_text())
            if not txt:
                continue
            classes = el.get("class") or []
            if "company" in classes or "boardPosition" in classes:
                continue
            if txt in {company, board_position, name}:
                continue
            bio_parts.append(txt)
    bio_el = detail.select_one(".biography, .bio, .description")
    if bio_el:
        b = clean(bio_el.get_text())
        if b and b not in bio_parts:
            bio_parts.append(b)
    bio = "\n\n".join(bio_parts).strip()

    labelled_links: dict[str, str] = {}
    for ul in detail.select(".rightWrapper > ul"):
        label = ""
        for li in ul.select("li"):
            label_p = li.select_one("p.label")
            if label_p:
                label = clean(label_p.get_text()).rstrip(":").strip().lower()
                continue
            link = li.select_one("a")
            if link and label:
                href = link.get("href") or ""
                if href and label not in labelled_links:
                    labelled_links[label] = href
            elif label and not link:
                txt = clean(li.get_text())
                if txt and label not in labelled_links:
                    labelled_links[label] = txt

    socials: dict[str, str] = {}
    for a in detail.select(".linkWrapper a, .socialMediaLink"):
        if a.name != "a":
            continue
        href = a.get("href")
        if not href:
            continue
        icon = a.select_one("i")
        platform = None
        if icon:
            icon_classes = icon.get("class") or []
            for plat, cls in SOCIAL_ICONS.items():
                if cls in icon_classes:
                    platform = plat
                    break
        if not platform:
            for plat in SOCIAL_ICONS.keys():
                if plat.replace("-", "") in href.lower().replace("-", ""):
                    platform = plat
                    break
        if platform and platform not in socials:
            socials[platform] = href

    talk_ids: list[str] = []
    for teaser in detail.select("div.agendaEventSlotTeaser"):
        tid = teaser.get("data-agenda-id")
        if tid and tid not in talk_ids:
            talk_ids.append(tid)

    return {
        "name": name,
        "company": company,
        "board_position": board_position,
        "photo_url": photo,
        "bio": bio,
        "labelled_links": labelled_links,
        "socials": socials,
        "talk_ids": talk_ids,
    }


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

@dataclass
class Plan:
    do_network: bool = True
    do_parse: bool = True


def network_phase(client: httpx.Client) -> tuple[list[dict], set[str]]:
    """Populate the cache. Returns (agenda_index, contributor_ids_seen)."""
    agenda_html = fetch_agenda(client)
    index = parse_agenda_index(agenda_html)
    print(f"\nAgenda parsed: {len(index)} sessions")
    print(f"Sessions with detail (event_slot_id): "
          f"{sum(1 for e in index if e['event_slot_id'])}\n")

    contributor_ids: set[str] = set()
    for i, entry in enumerate(index, start=1):
        esid = entry["event_slot_id"]
        if not esid:
            print(f"  [{i:3d}/{len(index)}] (no event_slot_id, skip detail) "
                  f"{entry['title'][:60]}")
            continue
        try:
            payload = fetch_detail(
                client,
                event_slot_id=esid,
                event_agenda_id=entry["agenda_id"],
                date_agenda_ts=entry.get("date_agenda_ts"),
            )
        except Exception as e:
            print(f"  [{i:3d}/{len(index)}] FAIL detail event_slot_id={esid}: {e}")
            continue
        # Pull contributor IDs from the cached payload
        try:
            detail = parse_detail_payload(payload)
            for s in detail["speakers"]:
                if s.get("contributor_id"):
                    contributor_ids.add(s["contributor_id"])
        except Exception as e:
            print(f"     ! parse of cached detail failed: {e}")

    print(f"\nUnique speaker contributor_ids discovered: {len(contributor_ids)}\n")

    for i, cid in enumerate(sorted(contributor_ids), start=1):
        try:
            fetch_speaker(client, cid)
        except Exception as e:
            print(f"  [{i:3d}/{len(contributor_ids)}] FAIL speaker contributor_id={cid}: {e}")

    return index, contributor_ids


def parse_phase() -> dict:
    """Build final JSON from cache only — no network."""
    if not AGENDA_CACHE.exists():
        raise SystemExit(
            f"Missing {AGENDA_CACHE} — run network phase first or omit --parse-only."
        )

    agenda_html = AGENDA_CACHE.read_text(encoding="utf-8")
    index = parse_agenda_index(agenda_html)

    talks: list[dict] = []
    contributor_ids: set[str] = set()
    for entry in index:
        esid = entry["event_slot_id"]
        detail_data = None
        if esid:
            detail_cache = DETAIL_DIR / f"{esid}.json"
            if detail_cache.exists():
                payload = json.loads(detail_cache.read_text(encoding="utf-8"))
                if payload.get("status") == 0:
                    detail_data = parse_detail_payload(payload)
                    for s in detail_data["speakers"]:
                        if s.get("contributor_id"):
                            contributor_ids.add(s["contributor_id"])
                else:
                    detail_data = {"error": f"status={payload.get('status')}", "raw_message": payload.get("message")}
        talks.append({**entry, "detail": detail_data})

    speakers: dict[str, dict] = {}
    for cid in sorted(contributor_ids):
        speaker_cache = SPEAKER_DIR / f"{cid}.json"
        if not speaker_cache.exists():
            speakers[cid] = {"contributor_id": cid, "error": "no cache"}
            continue
        payload = json.loads(speaker_cache.read_text(encoding="utf-8"))
        if payload.get("status") == 0:
            entry = parse_speaker_payload(payload)
            entry["contributor_id"] = cid
            speakers[cid] = entry
        else:
            speakers[cid] = {"contributor_id": cid, "error": f"status={payload.get('status')}"}

    days = sorted({t["date"] for t in talks})
    rooms = sorted({t["room"] for t in talks if t["room"]})

    return {
        "conference": {
            "name": "CloudLand 2026",
            "venue": "Heide Park Soltau, Germany",
            "host": "DOAG",
            "url": AGENDA_URL,
            "start_date": days[0] if days else None,
            "end_date": days[-1] if days else None,
            "timezone": "Europe/Berlin",
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "scraper_user_agent": USER_AGENT,
        },
        "days": days,
        "rooms": rooms,
        "talks": talks,
        "speakers": speakers,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--net-only", action="store_true", help="Only populate the cache; don't rebuild JSON.")
    parser.add_argument("--parse-only", action="store_true", help="Skip network; rebuild JSON from cache only.")
    args = parser.parse_args()

    if args.net_only and args.parse_only:
        print("--net-only and --parse-only are mutually exclusive", file=sys.stderr)
        return 2

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    DETAIL_DIR.mkdir(parents=True, exist_ok=True)
    SPEAKER_DIR.mkdir(parents=True, exist_ok=True)

    if not args.parse_only:
        headers = {"User-Agent": USER_AGENT}
        with httpx.Client(headers=headers, follow_redirects=True) as client:
            network_phase(client)

    if not args.net_only:
        out = parse_phase()
        payload = json.dumps(out, ensure_ascii=False, indent=2).encode("utf-8")
        with gzip.open(OUT_PATH, "wb") as f:
            f.write(payload)
        print(f"\nWrote {OUT_PATH} ({OUT_PATH.stat().st_size:,} bytes gzipped, {len(payload):,} bytes raw)")
        print(f"  talks:    {len(out['talks'])}")
        print(f"  speakers: {len(out['speakers'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
