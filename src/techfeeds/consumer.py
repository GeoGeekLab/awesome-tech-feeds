from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator, Mapping
from copy import deepcopy
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any, Literal, Self, cast
from xml.etree.ElementTree import Element, ElementTree, SubElement, indent

import httpx

QUERY_SCHEMA_VERSION = 1
QUERY_RESULT_SCHEMA_VERSION = 1
QUERY_ERROR_SCHEMA_VERSION = 1
PROFILE_RESULT_SCHEMA_VERSION = 1
SUPPORTED_REGISTRY_SCHEMA_VERSION = 2
SUPPORTED_SOURCE_SCHEMA_VERSION = 2
SUPPORTED_PROFILE_SCHEMA_VERSION = 2
DEFAULT_REGISTRY_URL = (
    "https://github.com/GeoGeekLab/awesome-tech-feeds/releases/latest/download/registry.json"
)

StatusFilter = Literal["active", "retired", "all"]


class ConsumerError(Exception):
    """Base error for the public consumer SDK."""

    code = "consumer_error"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": QUERY_ERROR_SCHEMA_VERSION,
            "error": {"code": self.code, "message": str(self)},
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


class RegistryLoadError(ConsumerError):
    """Raised when registry bytes cannot be loaded or decoded."""

    code = "registry_load_error"


class RegistryIntegrityError(ConsumerError):
    """Raised when registry bytes do not match an expected SHA-256 digest."""

    code = "registry_integrity_error"

    def __init__(self, *, expected: str, actual: str) -> None:
        self.expected = expected.lower()
        self.actual = actual.lower()
        super().__init__(f"registry SHA-256 mismatch: expected {self.expected}, got {self.actual}")

    def to_dict(self) -> dict[str, Any]:
        payload = super().to_dict()
        payload["error"].update({"expected": self.expected, "actual": self.actual})
        return payload


class RegistryCompatibilityError(ConsumerError):
    """Raised when a compiled registry uses an unsupported contract version."""

    code = "unsupported_registry_contract"

    def __init__(self, *, component: str, expected: int, actual: object) -> None:
        self.component = component
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"unsupported {component} schema version: expected {expected}, got {actual!r}"
        )

    def to_dict(self) -> dict[str, Any]:
        payload = super().to_dict()
        payload["error"].update(
            {"component": self.component, "expected": self.expected, "actual": self.actual}
        )
        return payload


class QueryError(ConsumerError, ValueError):
    """Base class for deterministic query validation failures."""

    code = "query_error"


class QueryContractError(QueryError):
    """Raised when a serialized query does not conform to query contract v1."""

    code = "invalid_query_contract"


class UnknownFilterValueError(QueryError):
    """Raised when a query references a value absent from the loaded registry."""

    code = "unknown_filter_value"

    def __init__(self, *, field: str, value: str, choices: tuple[str, ...]) -> None:
        self.field = field
        self.value = value
        self.choices = choices
        super().__init__(f"unknown {field}: {value}")

    def to_dict(self) -> dict[str, Any]:
        payload = super().to_dict()
        payload["error"].update(
            {"field": self.field, "value": self.value, "choices": list(self.choices)}
        )
        return payload


@dataclass(frozen=True, slots=True)
class Query:
    """Versioned, deterministic source query."""

    collection: str | None = None
    topics: tuple[str, ...] = ()
    traits: tuple[str, ...] = ()
    language: str | None = None
    kind: str | None = None
    status: StatusFilter = "active"

    def __post_init__(self) -> None:
        object.__setattr__(self, "topics", tuple(sorted(set(self.topics))))
        object.__setattr__(self, "traits", tuple(sorted(set(self.traits))))
        if self.status not in {"active", "retired", "all"}:
            raise QueryContractError(f"unsupported status filter: {self.status}")

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": QUERY_SCHEMA_VERSION,
            "status": self.status,
        }
        if self.collection is not None:
            payload["collection"] = self.collection
        if self.topics:
            payload["topics"] = list(self.topics)
        if self.traits:
            payload["traits"] = list(self.traits)
        if self.language is not None:
            payload["language"] = self.language
        if self.kind is not None:
            payload["kind"] = self.kind
        return payload

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> Self:
        allowed = {
            "schema_version",
            "collection",
            "topics",
            "traits",
            "language",
            "kind",
            "status",
        }
        unknown = sorted(set(value) - allowed)
        if unknown:
            raise QueryContractError(f"unknown query field(s): {', '.join(unknown)}")
        version = value.get("schema_version")
        if version != QUERY_SCHEMA_VERSION:
            raise QueryContractError(
                "unsupported query schema version: "
                f"expected {QUERY_SCHEMA_VERSION}, got {version!r}"
            )

        collection = _optional_string(value, "collection")
        topics = _string_tuple(value, "topics")
        traits = _string_tuple(value, "traits")
        language = _optional_string(value, "language")
        kind = _optional_string(value, "kind")
        status = value.get("status", "active")
        if not isinstance(status, str) or status not in {"active", "retired", "all"}:
            raise QueryContractError("query status must be one of: active, retired, all")
        return cls(
            collection=collection,
            topics=topics,
            traits=traits,
            language=language,
            kind=kind,
            status=cast(StatusFilter, status),
        )


class SourceRecord(Mapping[str, Any]):
    """Read-only mapping wrapper around one source record."""

    __slots__ = ("_data",)

    def __init__(self, data: Mapping[str, Any]) -> None:
        self._data = deepcopy(dict(data))

    @property
    def id(self) -> str:
        return str(self._data["id"])

    @property
    def name(self) -> str:
        return str(self._data["name"])

    @property
    def website(self) -> str:
        return str(self._data["website"])

    @property
    def status(self) -> str:
        return str(self._data["status"])

    def to_dict(self) -> dict[str, Any]:
        return deepcopy(self._data)

    def __getitem__(self, key: str) -> Any:
        return deepcopy(self._data[key])

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)


@dataclass(frozen=True, slots=True)
class QueryResult:
    """Immutable query result with stable JSON and OPML serializers."""

    query: Query
    registry_schema_version: int
    component_schema_versions: Mapping[str, int]
    sources: tuple[SourceRecord, ...]

    @property
    def count(self) -> int:
        return len(self.sources)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": QUERY_RESULT_SCHEMA_VERSION,
            "registry_schema_version": self.registry_schema_version,
            "component_schema_versions": dict(self.component_schema_versions),
            "query": self.query.to_dict(),
            "count": self.count,
            "sources": [source.to_dict() for source in self.sources],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"

    def to_opml(self, *, title: str | None = None) -> str:
        document_title = title or _query_title(self.query)
        return _sources_to_opml(document_title, self.sources)


class ProfileRecord(Mapping[str, Any]):
    """Read-only mapping wrapper around one profile policy."""

    __slots__ = ("_data",)

    def __init__(self, data: Mapping[str, Any]) -> None:
        self._data = deepcopy(dict(data))

    @property
    def id(self) -> str:
        return str(self._data["id"])

    @property
    def name(self) -> str:
        return str(self._data["name"])

    @property
    def description(self) -> str:
        return str(self._data["description"])

    def to_dict(self) -> dict[str, Any]:
        return deepcopy(self._data)

    def __getitem__(self, key: str) -> Any:
        return deepcopy(self._data[key])

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)


@dataclass(frozen=True, slots=True)
class ProfileSource:
    """A source resolved by a profile with explainable priority metadata."""

    source: SourceRecord
    priority_score: int
    matched_boost_topics: tuple[str, ...]
    matched_boost_traits: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "priority_score": self.priority_score,
            "matched_boost_topics": list(self.matched_boost_topics),
            "matched_boost_traits": list(self.matched_boost_traits),
            "source": self.source.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class ProfileResult:
    """Deterministic resolution of a Profile Contract v2 policy."""

    profile: ProfileRecord
    registry_schema_version: int
    component_schema_versions: Mapping[str, int]
    budget: Mapping[str, int]
    candidate_count: int
    excluded_count: int
    sources: tuple[ProfileSource, ...]

    @property
    def count(self) -> int:
        return len(self.sources)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": PROFILE_RESULT_SCHEMA_VERSION,
            "registry_schema_version": self.registry_schema_version,
            "component_schema_versions": dict(self.component_schema_versions),
            "profile": self.profile.to_dict(),
            "budget": dict(self.budget),
            "resolution": {
                "candidate_count": self.candidate_count,
                "excluded_count": self.excluded_count,
                "selected_count": self.count,
                "ordering": "boost-score-desc-then-first-appearance",
                "exclude_precedence": "exclude-before-boost",
            },
            "count": self.count,
            "sources": [item.to_dict() for item in self.sources],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"

    def to_opml(self, *, title: str | None = None) -> str:
        document_title = title or f"Awesome Tech Feeds — Profile: {self.profile.name}"
        return _sources_to_opml(
            document_title,
            tuple(item.source for item in self.sources),
        )


class Registry:
    """Compiled-registry consumer that is independent from repository source files."""

    __slots__ = (
        "_collections",
        "_component_schema_versions",
        "_profile_schema_version",
        "_profiles",
        "_registry_schema_version",
        "_sources",
    )

    def __init__(self, payload: Mapping[str, Any]) -> None:
        data = deepcopy(dict(payload))
        registry_version = data.get("schema_version")
        if registry_version != SUPPORTED_REGISTRY_SCHEMA_VERSION:
            raise RegistryCompatibilityError(
                component="registry",
                expected=SUPPORTED_REGISTRY_SCHEMA_VERSION,
                actual=registry_version,
            )
        component_versions = data.get("component_schema_versions")
        if not isinstance(component_versions, dict):
            raise RegistryLoadError("registry component_schema_versions must be an object")
        source_version = component_versions.get("source")
        if source_version != SUPPORTED_SOURCE_SCHEMA_VERSION:
            raise RegistryCompatibilityError(
                component="source",
                expected=SUPPORTED_SOURCE_SCHEMA_VERSION,
                actual=source_version,
            )

        source_values = data.get("sources")
        collection_values = data.get("collections")
        profile_values = data.get("profiles")
        if not isinstance(source_values, list) or not all(
            isinstance(item, dict) for item in source_values
        ):
            raise RegistryLoadError("registry sources must be an array of objects")
        if not isinstance(collection_values, list) or not all(
            isinstance(item, dict) for item in collection_values
        ):
            raise RegistryLoadError("registry collections must be an array of objects")
        if not isinstance(profile_values, list) or not all(
            isinstance(item, dict) for item in profile_values
        ):
            raise RegistryLoadError("registry profiles must be an array of objects")

        self._registry_schema_version = registry_version
        try:
            self._component_schema_versions = {
                str(key): int(value) for key, value in component_versions.items()
            }
        except (TypeError, ValueError) as exc:
            raise RegistryLoadError("component schema versions must be integers") from exc
        self._profile_schema_version = self._component_schema_versions.get("profile", 1)
        self._sources = tuple(SourceRecord(item) for item in source_values)
        self._collections = {
            str(item["id"]): tuple(str(source_id) for source_id in item["sources"])
            for item in collection_values
        }
        self._profiles = {str(item["id"]): ProfileRecord(item) for item in profile_values}

    @property
    def schema_version(self) -> int:
        return self._registry_schema_version

    @property
    def component_schema_versions(self) -> dict[str, int]:
        return dict(self._component_schema_versions)

    @property
    def collections(self) -> tuple[str, ...]:
        return tuple(sorted(self._collections))

    @property
    def sources(self) -> tuple[SourceRecord, ...]:
        return tuple(SourceRecord(source.to_dict()) for source in self._sources)

    @property
    def profiles(self) -> tuple[str, ...]:
        return tuple(sorted(self._profiles))

    def profile(self, profile_id: str) -> ProfileRecord | None:
        profile = self._profiles.get(profile_id)
        if profile is None:
            return None
        return ProfileRecord(profile.to_dict())

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> Self:
        return cls(payload)

    @classmethod
    def from_file(cls, path: str | Path, *, expected_sha256: str | None = None) -> Self:
        file_path = Path(path)
        try:
            raw = file_path.read_bytes()
        except OSError as exc:
            raise RegistryLoadError(f"could not read registry file {file_path}: {exc}") from exc
        return cls._from_bytes(raw, expected_sha256=expected_sha256)

    @classmethod
    def from_url(
        cls,
        url: str = DEFAULT_REGISTRY_URL,
        *,
        timeout: float = 10.0,
        expected_sha256: str | None = None,
    ) -> Self:
        try:
            response = httpx.get(url, follow_redirects=True, timeout=timeout)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RegistryLoadError(f"could not fetch registry URL {url}: {exc}") from exc
        return cls._from_bytes(response.content, expected_sha256=expected_sha256)

    @classmethod
    def _from_bytes(cls, raw: bytes, *, expected_sha256: str | None) -> Self:
        if expected_sha256 is not None:
            actual = hashlib.sha256(raw).hexdigest()
            if actual.lower() != expected_sha256.lower():
                raise RegistryIntegrityError(expected=expected_sha256, actual=actual)
        try:
            payload = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RegistryLoadError(f"registry is not valid UTF-8 JSON: {exc}") from exc
        if not isinstance(payload, dict):
            raise RegistryLoadError("registry JSON root must be an object")
        return cls(payload)

    def get(self, source_id: str) -> SourceRecord | None:
        for source in self._sources:
            if source.id == source_id:
                return SourceRecord(source.to_dict())
        return None

    def query(self, query: Query | None = None) -> QueryResult:
        requested = query or Query()
        self._validate_query(requested)

        by_id = {source.id: source for source in self._sources}
        if requested.collection is None:
            candidates = sorted(self._sources, key=lambda source: source.id)
        else:
            candidates = [
                by_id[source_id]
                for source_id in self._collections[requested.collection]
                if source_id in by_id
            ]

        topics = set(requested.topics)
        traits = set(requested.traits)
        selected: list[SourceRecord] = []
        for source in candidates:
            data = source.to_dict()
            if requested.status != "all" and data["status"] != requested.status:
                continue
            if not topics.issubset(set(data["topics"])):
                continue
            if not traits.issubset(set(data["traits"])):
                continue
            if requested.language is not None and data["language"] != requested.language:
                continue
            if requested.kind is not None and data["kind"] != requested.kind:
                continue
            selected.append(SourceRecord(data))

        return QueryResult(
            query=requested,
            registry_schema_version=self._registry_schema_version,
            component_schema_versions=self._component_schema_versions,
            sources=tuple(selected),
        )

    def resolve_profile(self, profile_id: str) -> ProfileResult:
        """Resolve Profile Contract v2 into an ordered, explainable active-source set."""
        if self._profile_schema_version != SUPPORTED_PROFILE_SCHEMA_VERSION:
            raise RegistryCompatibilityError(
                component="profile",
                expected=SUPPORTED_PROFILE_SCHEMA_VERSION,
                actual=self._profile_schema_version,
            )
        profile = self._profiles.get(profile_id)
        if profile is None:
            raise UnknownFilterValueError(
                field="profile",
                value=profile_id,
                choices=tuple(sorted(self._profiles)),
            )

        profile_data = profile.to_dict()
        by_id = {source.id: source for source in self._sources}
        candidate_ids: list[str] = []
        seen: set[str] = set()
        for collection_id in profile_data["collections"]:
            members = self._collections.get(str(collection_id))
            if members is None:
                raise RegistryLoadError(
                    f"profile {profile_id} references unknown collection {collection_id}"
                )
            for source_id in members:
                if source_id not in seen:
                    seen.add(source_id)
                    candidate_ids.append(source_id)

        boost = profile_data["boost"]
        exclude = profile_data["exclude"]
        boost_topics = tuple(str(value) for value in boost["topics"])
        boost_traits = tuple(str(value) for value in boost["traits"])
        exclude_topics = set(str(value) for value in exclude["topics"])
        exclude_traits = set(str(value) for value in exclude["traits"])
        exclude_sources = set(str(value) for value in exclude["sources"])

        candidate_count = 0
        excluded_count = 0
        ranked: list[tuple[int, ProfileSource]] = []
        for position, source_id in enumerate(candidate_ids):
            source = by_id.get(source_id)
            if source is None:
                continue
            data = source.to_dict()
            if data["status"] != "active":
                continue
            candidate_count += 1
            source_topics = set(str(value) for value in data["topics"])
            source_traits = set(str(value) for value in data["traits"])
            if (
                source_id in exclude_sources
                or source_topics.intersection(exclude_topics)
                or source_traits.intersection(exclude_traits)
            ):
                excluded_count += 1
                continue

            matched_topics = tuple(value for value in boost_topics if value in source_topics)
            matched_traits = tuple(value for value in boost_traits if value in source_traits)
            ranked.append(
                (
                    position,
                    ProfileSource(
                        source=SourceRecord(data),
                        priority_score=len(matched_topics) + len(matched_traits),
                        matched_boost_topics=matched_topics,
                        matched_boost_traits=matched_traits,
                    ),
                )
            )

        ranked.sort(key=lambda item: (-item[1].priority_score, item[0]))
        return ProfileResult(
            profile=ProfileRecord(profile_data),
            registry_schema_version=self._registry_schema_version,
            component_schema_versions=self._component_schema_versions,
            budget={
                "recommended_daily_items": int(profile_data["budget"]["recommended_daily_items"])
            },
            candidate_count=candidate_count,
            excluded_count=excluded_count,
            sources=tuple(item for _, item in ranked),
        )

    def _validate_query(self, query: Query) -> None:
        dimensions: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
            ("topic", query.topics, self._known_values("topics")),
            ("trait", query.traits, self._known_values("traits")),
        )
        for field, values, choices in dimensions:
            known = set(choices)
            for value in values:
                if value not in known:
                    raise UnknownFilterValueError(field=field, value=value, choices=choices)

        if query.collection is not None and query.collection not in self._collections:
            choices = tuple(sorted(self._collections))
            raise UnknownFilterValueError(
                field="collection", value=query.collection, choices=choices
            )
        if query.language is not None:
            self._validate_scalar("language", query.language, self._known_values("language"))
        if query.kind is not None:
            self._validate_scalar("kind", query.kind, self._known_values("kind"))

    def _known_values(self, field: str) -> tuple[str, ...]:
        values: set[str] = set()
        for source in self._sources:
            value = source.to_dict()[field]
            if isinstance(value, list):
                values.update(str(item) for item in value)
            else:
                values.add(str(value))
        return tuple(sorted(values))

    @staticmethod
    def _validate_scalar(field: str, value: str, choices: tuple[str, ...]) -> None:
        if value not in set(choices):
            raise UnknownFilterValueError(field=field, value=value, choices=choices)


def _optional_string(value: Mapping[str, Any], field: str) -> str | None:
    item = value.get(field)
    if item is None:
        return None
    if not isinstance(item, str) or not item:
        raise QueryContractError(f"query {field} must be a non-empty string")
    return item


def _string_tuple(value: Mapping[str, Any], field: str) -> tuple[str, ...]:
    item = value.get(field, [])
    if not isinstance(item, list) or not all(isinstance(part, str) and part for part in item):
        raise QueryContractError(f"query {field} must be an array of non-empty strings")
    return tuple(item)


def _query_title(query: Query) -> str:
    if query.collection is not None:
        return f"Awesome Tech Feeds — {query.collection}"
    return "Awesome Tech Feeds — Query"


def _sources_to_opml(title: str, sources: tuple[SourceRecord, ...]) -> str:
    opml = Element("opml", {"version": "2.0"})
    head = SubElement(opml, "head")
    SubElement(head, "title").text = title
    body = SubElement(opml, "body")
    for source in sources:
        data = source.to_dict()
        feed = next(item for item in data["feeds"] if item["role"] == "primary")
        SubElement(
            body,
            "outline",
            {
                "type": "rss",
                "text": str(data["name"]),
                "title": str(data["name"]),
                "xmlUrl": str(feed["url"]),
                "htmlUrl": str(data["website"]),
                "techFeedsId": str(data["id"]),
            },
        )
    indent(opml, space="  ")
    buffer = BytesIO()
    ElementTree(opml).write(buffer, encoding="utf-8", xml_declaration=True)
    return buffer.getvalue().decode("utf-8")
