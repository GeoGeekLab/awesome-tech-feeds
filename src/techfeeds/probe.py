from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

import httpx

from .compile import load_sources
from .io import dump_json
from .models import ProbeResult

USER_AGENT = "awesome-tech-feeds-health/0.1 (+https://github.com/GeoGeekLab/awesome-tech-feeds)"


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    value = value.strip()
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except (ValueError, TypeError):
        pass
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (ValueError, TypeError, OverflowError):
        return None


def parse_feed(
    content: bytes, content_type: str = ""
) -> tuple[bool, str, int, str | None, str | None]:
    text = content.lstrip()
    if "json" in content_type.lower() or text.startswith(b"{"):
        data = json.loads(content)
        items = data.get("items", []) if isinstance(data, dict) else []
        dates: list[datetime] = []
        for item in items[:50]:
            if not isinstance(item, dict):
                continue
            for key in ("date_published", "date_modified"):
                parsed = _parse_date(item.get(key))
                if parsed:
                    dates.append(parsed)
        latest = max(dates).isoformat() if dates else None
        return True, "jsonfeed", len(items), latest, None

    root = ET.fromstring(content)
    tag = root.tag.lower()
    dates = []

    if tag.endswith("rss") or tag.endswith("rdf"):
        items = root.findall(".//item")
        for item in items[:50]:
            for child in list(item):
                child_name = child.tag.lower()
                if child_name.endswith(("pubdate", "date", "updated")):
                    parsed = _parse_date(child.text)
                    if parsed:
                        dates.append(parsed)
        latest = max(dates).isoformat() if dates else None
        return True, "rss", len(items), latest, None

    if tag.endswith("feed"):
        namespace = ""
        if root.tag.startswith("{"):
            namespace = root.tag.split("}", 1)[0] + "}"
        entries = root.findall(f"{namespace}entry")
        for entry in entries[:50]:
            for key in ("published", "updated"):
                child = entry.find(f"{namespace}{key}")
                parsed = _parse_date(child.text if child is not None else None)
                if parsed:
                    dates.append(parsed)
        latest = max(dates).isoformat() if dates else None
        return True, "atom", len(entries), latest, None

    return False, "unknown", 0, None, f"unsupported root element: {root.tag}"


def classify_health(status: int | None, valid: bool, item_count: int, error: str | None) -> str:
    if error or status is None or status >= 500:
        return "broken"
    if status in {401, 403, 429} or status >= 400:
        return "degraded"
    if not valid:
        return "broken"
    if item_count == 0:
        return "stale"
    return "healthy"


async def probe_one(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    source_id: str,
    feed_url: str,
    previous: dict[str, Any] | None = None,
) -> dict[str, Any]:
    headers = {"User-Agent": USER_AGENT}
    if previous:
        if previous.get("etag"):
            headers["If-None-Match"] = str(previous["etag"])
        if previous.get("last_modified"):
            headers["If-Modified-Since"] = str(previous["last_modified"])

    started = time.perf_counter()
    checked_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    async with semaphore:
        try:
            response = await client.get(feed_url, headers=headers, follow_redirects=True)
            latency_ms = int((time.perf_counter() - started) * 1000)
            if response.status_code == 304 and previous:
                result = dict(previous)
                result.update(
                    checked_at=checked_at,
                    http_status=304,
                    latency_ms=latency_ms,
                )
                return result

            try:
                valid, feed_format, item_count, latest_item_at, parse_error = parse_feed(
                    response.content, response.headers.get("content-type", "")
                )
            except (ET.ParseError, json.JSONDecodeError, UnicodeError, ValueError) as exc:
                valid = False
                feed_format = None
                item_count = 0
                latest_item_at = None
                parse_error = f"{type(exc).__name__}: {exc}"

            return ProbeResult(
                source_id=source_id,
                feed_url=feed_url,
                checked_at=checked_at,
                http_status=response.status_code,
                latency_ms=latency_ms,
                valid=valid,
                format=feed_format,
                item_count=item_count,
                latest_item_at=latest_item_at,
                etag=response.headers.get("etag"),
                last_modified=response.headers.get("last-modified"),
                final_url=str(response.url),
                error=parse_error,
                health=classify_health(response.status_code, valid, item_count, parse_error),
            ).to_dict()
        except httpx.HTTPError as exc:
            latency_ms = int((time.perf_counter() - started) * 1000)
            return ProbeResult(
                source_id=source_id,
                feed_url=feed_url,
                checked_at=checked_at,
                http_status=None,
                latency_ms=latency_ms,
                valid=False,
                error=f"{type(exc).__name__}: {exc}",
                health="broken",
            ).to_dict()


async def probe_registry(root: Path, concurrency: int = 8) -> dict[str, Any]:
    previous: dict[str, dict[str, Any]] = {}
    health_path = root / "generated" / "health.json"
    if health_path.exists():
        try:
            data = json.loads(health_path.read_text(encoding="utf-8"))
            previous = {item["feed_url"]: item for item in data.get("feeds", [])}
        except (json.JSONDecodeError, KeyError, TypeError):
            previous = {}

    sources = load_sources(root)
    semaphore = asyncio.Semaphore(max(1, concurrency))
    timeout = httpx.Timeout(15.0, connect=8.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        jobs = []
        for source in sources:
            if source["status"] != "active":
                continue
            for feed in source["feeds"]:
                jobs.append(
                    probe_one(
                        client,
                        semaphore,
                        str(source["id"]),
                        str(feed["url"]),
                        previous.get(str(feed["url"])),
                    )
                )
        results = await asyncio.gather(*jobs)

    states = ("healthy", "degraded", "stale", "broken")
    counts = {state: sum(item["health"] == state for item in results) for state in states}
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "counts": counts,
        "feeds": sorted(results, key=lambda item: (item["source_id"], item["feed_url"])),
    }
    dump_json(health_path, payload)
    return payload
