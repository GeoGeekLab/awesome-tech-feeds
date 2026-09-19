from __future__ import annotations

import json
from collections import defaultdict
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
    feed_owners: dict[str, list[str]] = defaultdict(list)
    website_owners: dict[str, list[str]] = defaultdict(list)

    for path in iter_yaml(root, "sources"):
        data = load_yaml(path)
        errors.extend(_schema_errors(source_validator, data, path, root))
        if not isinstance(data, dict):
            continue

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
        for source_id in data.get("sources", []):
            if source_id not in source_ids:
                errors.append(f"{path.relative_to(root)}: unknown source {source_id}")

    for path in iter_yaml(root, "profiles"):
        data = load_yaml(path)
        errors.extend(_schema_errors(profile_validator, data, path, root))
        if not isinstance(data, dict):
            continue
        profile_id = data.get("id")
        if isinstance(profile_id, str) and path.stem != profile_id:
            errors.append(
                f"{path.relative_to(root)}: filename must match profile id {profile_id!r}"
            )
        for collection_id in data.get("collections", []):
            if collection_id not in collection_ids:
                errors.append(f"{path.relative_to(root)}: unknown collection {collection_id}")
        for topic in data.get("boost_topics", []):
            if topic not in topics:
                errors.append(f"{path.relative_to(root)}: unknown topic {topic}")
        for trait in data.get("exclude_traits", []):
            if trait not in traits:
                errors.append(f"{path.relative_to(root)}: unknown trait {trait}")

    return errors


def require_valid_registry(root: Path) -> None:
    errors = validate_registry(root)
    if errors:
        raise RegistryValidationError("Registry invalid:\n" + "\n".join(errors))
