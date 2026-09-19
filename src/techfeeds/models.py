from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ProbeResult:
    source_id: str
    feed_url: str
    checked_at: str
    http_status: int | None
    latency_ms: int | None
    valid: bool
    format: str | None = None
    item_count: int = 0
    latest_item_at: str | None = None
    etag: str | None = None
    last_modified: str | None = None
    final_url: str | None = None
    error: str | None = None
    health: str = "broken"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
