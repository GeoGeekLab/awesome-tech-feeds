from __future__ import annotations

import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from jsonschema import Draft202012Validator, FormatChecker

from .io import iter_yaml, load_yaml


class RegistryValidationError(ValueError):
    """Raised when the registry violates a deterministic contract."""


def _validator(root: Path, name: str) -> Draft202012Validator:
    schema = json.loads((root / "schema" / name).read_text(encoding="utf-8"))
    return Draft202012Validator(schema, format_checker=FormatChecker())


def _canonical_url(url: str) -> str:
    parts = urlsplit(url.strip())
    path = parts.path or "/"
    if path != "/":
        path = path.rstrip("/")
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, parts.query, ""))


def _schema_errors(validator: Draft202012Validator, data: Any, path: Path, root: Path) -> list[str]:
    errors: list[str] = []
    for error in sorted(validator.iter_errors(data), key=lambda item: list(item.path)):
        location = ".".join(str(part) for part in error.path)
        prefix = f"{path.relative_to(root)}"
        if location:
            prefix += f":{location}"
        errors.append(f"{prefix}: {error.message}")
    return errors


def _date_value(value: Any) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _source_contract_errors(data: dict[str, Any], path: Path, root: Path) -> list[str]:
    errors: list[str] = []
    prefix = str(path.relative_to(root))
    curation = data.get("curation")
    provenance = data.get("provenance")
    if not isinstance(curation, dict) or not isinstance(provenance, dict):
        return errors

    reviewed_at = _date_value(curation.get("reviewed_at"))
    review_after = _date_value(curation.get("review_after"))
    added_at = _date_value(provenance.get("added_at"))

    if reviewed_at is not None and review_after is not None:
        interval = (review_after - reviewed_at).days
        if interval < 30 or interval > 366:
            errors.append(
                f"{prefix}: review_after must be 30 to 366 days after reviewed_at; "
                f"found {interval} days"
            )
    if added_at is not None and reviewed_at is not None and added_at > reviewed_at:
        errors.append(f"{prefix}: provenance added_at must not be after curation reviewed_at")

    evidence = provenance.get("evidence")
    if not isinstance(evidence, list):
        return errors

    website = data.get("website")
    identity_urls = {
        _canonical_url(item["url"])
        for item in evidence
        if isinstance(item, dict)
        and item.get("type") == "identity"
        and isinstance(item.get("url"), str)
    }
    if isinstance(website, str) and _canonical_url(website) not in identity_urls:
        errors.append(
            f"{prefix}: provenance evidence must include the canonical website as identity"
        )

    primary_urls = {
        _canonical_url(feed["url"])
        for feed in data.get("feeds", [])
        if isinstance(feed, dict)
        and feed.get("role") == "primary"
        and isinstance(feed.get("url"), str)
    }
    feed_urls = {
        _canonical_url(item["url"])
        for item in evidence
        if isinstance(item, dict)
        and item.get("type") == "feed"
        and isinstance(item.get("url"), str)
    }
    if primary_urls and not primary_urls.intersection(feed_urls):
        errors.append(f"{prefix}: provenance evidence must include the primary feed URL")

    return errors


def validate_registry(root: Path) -> list[str]:
    errors: list[str] = []
    source_validator = _validator(root, "source.schema.json")
    collection_validator = _validator(root, "collection.schema.json")
    profile_validator = _validator(root, "profile.schema.json")

    topics_data = load_yaml(root / "registry" / "topics.yaml")
    traits_data = load_yaml(root / "registry" / "traits.yaml")
    languages_data = load_yaml(root / "registry" / "languages.yaml")
    topics = set(topics_data)
    traits = set(traits_data)
    languages = set(languages_data)

    source_ids: dict[str, Path] = {}
    source_records: dict[str, dict[str, Any]] = {}
    feed_owners: dict[str, list[str]] = defaultdict(list)
    website_owners: dict[str, list[str]] = defaultdict(list)

    for path in iter_yaml(root, "sources"):
        data = load_yaml(path)
        errors.extend(_schema_errors(source_validator, data, path, root))
        if not isinstance(data, dict):
            continue
        errors.extend(_source_contract_errors(data, path, root))

        source_id = data.get("id")
        if not isinstance(source_id, str):
            continue

        if path.stem != source_id:
            errors.append(f"{path.relative_to(root)}: filename must match source id {source_id!r}")

        if source_id in source_ids:
            errors.append(
                f"duplicate source id {source_id}: "
                f"{source_ids[source_id].relative_to(root)} and {path.relative_to(root)}"
            )
        source_ids[source_id] = path
        source_records[source_id] = data

        language = data.get("language")
        if isinstance(language, str) and language not in languages:
            errors.append(f"{path.relative_to(root)}: unknown language {language}")

        for topic in data.get("topics", []):
            if topic not in topics:
                errors.append(f"{path.relative_to(root)}: unknown topic {topic}")
        for trait in data.get("traits", []):
            if trait not in traits:
                errors.append(f"{path.relative_to(root)}: unknown trait {trait}")

        primary_count = 0
        for feed in data.get("feeds", []):
            if feed.get("role") == "primary":
                primary_count += 1
            feed_url = feed.get("url")
            if isinstance(feed_url, str):
                feed_owners[_canonical_url(feed_url)].append(source_id)
        if data.get("status") == "active" and primary_count != 1:
            errors.append(
                f"{path.relative_to(root)}: active source must have exactly one primary feed; "
                f"found {primary_count}"
            )

        website = data.get("website")
        if isinstance(website, str):
            website_owners[_canonical_url(website)].append(source_id)

    for url, owners in sorted(feed_owners.items()):
        if len(owners) > 1:
            errors.append(f"duplicate feed URL {url}: {', '.join(sorted(owners))}")
    for url, owners in sorted(website_owners.items()):
        if len(owners) > 1:
            errors.append(f"duplicate website URL {url}: {', '.join(sorted(owners))}")

    collection_ids: set[str] = set()
    collection_sources: dict[str, tuple[str, ...]] = {}
    for path in iter_yaml(root, "collections"):
        data = load_yaml(path)
        errors.extend(_schema_errors(collection_validator, data, path, root))
        if not isinstance(data, dict):
            continue
        collection_id = data.get("id")
        if isinstance(collection_id, str):
            collection_ids.add(collection_id)
            if path.stem != collection_id:
                errors.append(
                    f"{path.relative_to(root)}: filename must match collection id {collection_id!r}"
                )

        source_refs = data.get("sources", [])
        if not isinstance(source_refs, list):
            source_refs = []
        if isinstance(collection_id, str):
            collection_sources[collection_id] = tuple(
                str(source_id) for source_id in source_refs if isinstance(source_id, str)
            )
        for source_id in source_refs:
            if source_id not in source_ids:
                errors.append(f"{path.relative_to(root)}: unknown source {source_id}")

        policy = data.get("policy", {})
        if not isinstance(policy, dict):
            policy = {}
        max_sources = policy.get("max_sources")
        if isinstance(max_sources, int) and len(source_refs) > max_sources:
            errors.append(
                f"{path.relative_to(root)}: collection has {len(source_refs)} sources; "
                f"exceeds policy max_sources={max_sources}"
            )

        rationales = data.get("selection_rationale", {})
        if not isinstance(rationales, dict):
            rationales = {}
        extra_rationales = sorted(set(rationales) - set(source_refs))
        for source_id in extra_rationales:
            errors.append(
                f"{path.relative_to(root)}: selection rationale references non-member {source_id}"
            )
        if policy.get("require_rationale") is True:
            missing_rationales = [
                source_id
                for source_id in source_refs
                if not isinstance(rationales.get(source_id), str)
                or not rationales[source_id].strip()
            ]
            for source_id in missing_rationales:
                errors.append(
                    f"{path.relative_to(root)}: missing selection rationale for {source_id}"
                )

    for path in iter_yaml(root, "profiles"):
        data = load_yaml(path)
        errors.extend(_schema_errors(profile_validator, data, path, root))
        if not isinstance(data, dict):
            continue
        profile_id = data.get("id")
        prefix = str(path.relative_to(root))
        if isinstance(profile_id, str) and path.stem != profile_id:
            errors.append(f"{prefix}: filename must match profile id {profile_id!r}")

        selected_collections = data.get("collections", [])
        if not isinstance(selected_collections, list):
            selected_collections = []
        candidate_ids: list[str] = []
        seen_candidates: set[str] = set()
        for collection_id in selected_collections:
            if collection_id not in collection_ids:
                errors.append(f"{prefix}: unknown collection {collection_id}")
                continue
            for source_id in collection_sources.get(str(collection_id), ()):
                if source_id not in seen_candidates:
                    seen_candidates.add(source_id)
                    candidate_ids.append(source_id)

        boost = data.get("boost", {})
        exclude = data.get("exclude", {})
        if not isinstance(boost, dict):
            boost = {}
        if not isinstance(exclude, dict):
            exclude = {}

        boost_topics = boost.get("topics", [])
        boost_traits = boost.get("traits", [])
        exclude_topics = exclude.get("topics", [])
        exclude_traits = exclude.get("traits", [])
        exclude_sources = exclude.get("sources", [])
        if not isinstance(boost_topics, list):
            boost_topics = []
        if not isinstance(boost_traits, list):
            boost_traits = []
        if not isinstance(exclude_topics, list):
            exclude_topics = []
        if not isinstance(exclude_traits, list):
            exclude_traits = []
        if not isinstance(exclude_sources, list):
            exclude_sources = []

        for topic in [*boost_topics, *exclude_topics]:
            if topic not in topics:
                errors.append(f"{prefix}: unknown topic {topic}")
        for trait in [*boost_traits, *exclude_traits]:
            if trait not in traits:
                errors.append(f"{prefix}: unknown trait {trait}")
        for source_id in exclude_sources:
            if source_id not in source_ids:
                errors.append(f"{prefix}: unknown excluded source {source_id}")
            elif source_id not in seen_candidates:
                errors.append(
                    f"{prefix}: excluded source {source_id} is not selected by profile collections"
                )

        for topic in sorted(set(boost_topics).intersection(exclude_topics)):
            errors.append(f"{prefix}: topic {topic} cannot be both boosted and excluded")
        for trait in sorted(set(boost_traits).intersection(exclude_traits)):
            errors.append(f"{prefix}: trait {trait} cannot be both boosted and excluded")

        candidate_records = [
            source_records[source_id]
            for source_id in candidate_ids
            if source_id in source_records
        ]
        for topic in boost_topics:
            if topic in topics and not any(topic in source.get("topics", []) for source in candidate_records):
                errors.append(f"{prefix}: boost topic {topic} matches no selected source")
        for trait in boost_traits:
            if trait in traits and not any(trait in source.get("traits", []) for source in candidate_records):
                errors.append(f"{prefix}: boost trait {trait} matches no selected source")
        for topic in exclude_topics:
            if topic in topics and not any(topic in source.get("topics", []) for source in candidate_records):
                errors.append(f"{prefix}: exclude topic {topic} matches no selected source")
        for trait in exclude_traits:
            if trait in traits and not any(trait in source.get("traits", []) for source in candidate_records):
                errors.append(f"{prefix}: exclude trait {trait} matches no selected source")

    return errors


def require_valid_registry(root: Path) -> None:
    errors = validate_registry(root)
    if errors:
        raise RegistryValidationError("Registry invalid:\n" + "\n".join(errors))
