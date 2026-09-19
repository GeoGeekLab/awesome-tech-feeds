from __future__ import annotations

import asyncio

import httpx

from techfeeds.probe import classify_health, parse_feed, probe_one


def test_parse_rss_atom_and_json_feed() -> None:
    rss = (
        b"<?xml version='1.0'?><rss><channel><item>"
        b"<pubDate>Fri, 19 Sep 2026 10:00:00 GMT</pubDate></item></channel></rss>"
    )
    valid, feed_format, count, latest, error = parse_feed(rss, "application/rss+xml")
    assert (valid, feed_format, count, error) == (True, "rss", 1, None)
    assert latest is not None

    atom = (
        b"<feed xmlns='http://www.w3.org/2005/Atom'><entry>"
        b"<updated>2026-09-19T10:00:00Z</updated></entry></feed>"
    )
    valid, feed_format, count, latest, error = parse_feed(atom, "application/atom+xml")
    assert (valid, feed_format, count, error) == (True, "atom", 1, None)
    assert latest is not None

    json_feed = (
        b'{"version":"https://jsonfeed.org/version/1.1","items":'
        b'[{"date_published":"2026-09-19T10:00:00Z"}]}'
    )
    valid, feed_format, count, latest, error = parse_feed(json_feed, "application/feed+json")
    assert (valid, feed_format, count, error) == (True, "jsonfeed", 1, None)
    assert latest is not None


def test_health_classification() -> None:
    assert classify_health(200, True, 3, None) == "healthy"
    assert classify_health(200, True, 0, None) == "stale"
    assert classify_health(429, False, 0, None) == "degraded"
    assert classify_health(500, False, 0, "boom") == "broken"


def test_probe_uses_conditional_headers_and_preserves_304() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["if-none-match"] == '"abc"'
        return httpx.Response(304, request=request)

    async def run() -> dict[str, object]:
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            return await probe_one(
                client,
                asyncio.Semaphore(1),
                "example",
                "https://example.com/feed.xml",
                {
                    "source_id": "example",
                    "feed_url": "https://example.com/feed.xml",
                    "checked_at": "2026-09-19T00:00:00+00:00",
                    "http_status": 200,
                    "latency_ms": 1,
                    "valid": True,
                    "format": "rss",
                    "item_count": 2,
                    "latest_item_at": None,
                    "etag": '"abc"',
                    "last_modified": None,
                    "final_url": "https://example.com/feed.xml",
                    "error": None,
                    "health": "healthy",
                },
            )

    result = asyncio.run(run())
    assert result["http_status"] == 304
    assert result["health"] == "healthy"
    assert result["item_count"] == 2


def test_probe_success_and_http_error() -> None:
    async def ok_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            request=request,
            headers={"content-type": "application/rss+xml", "etag": '"v1"'},
            content=(
                b"<rss><channel><item>"
                b"<pubDate>Fri, 19 Sep 2026 10:00:00 GMT</pubDate>"
                b"</item></channel></rss>"
            ),
        )

    async def fail_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline", request=request)

    async def run() -> tuple[dict[str, object], dict[str, object]]:
        async with httpx.AsyncClient(transport=httpx.MockTransport(ok_handler)) as client:
            ok = await probe_one(
                client,
                asyncio.Semaphore(1),
                "example",
                "https://example.com/feed.xml",
            )
        async with httpx.AsyncClient(transport=httpx.MockTransport(fail_handler)) as client:
            failed = await probe_one(
                client,
                asyncio.Semaphore(1),
                "example",
                "https://example.com/feed.xml",
            )
        return ok, failed

    ok, failed = asyncio.run(run())
    assert ok["health"] == "healthy"
    assert ok["format"] == "rss"
    assert ok["etag"] == '"v1"'
    assert failed["health"] == "broken"
    assert failed["http_status"] is None


def test_parse_unknown_and_invalid_dates() -> None:
    valid, feed_format, count, latest, error = parse_feed(b"<html></html>", "text/xml")
    assert (valid, feed_format, count, latest) == (False, "unknown", 0, None)
    assert error is not None

    rss = b"<rss><channel><item><pubDate>not-a-date</pubDate></item></channel></rss>"
    valid, feed_format, count, latest, error = parse_feed(rss, "application/rss+xml")
    assert (valid, feed_format, count, latest, error) == (True, "rss", 1, None, None)
