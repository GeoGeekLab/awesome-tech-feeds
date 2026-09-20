from __future__ import annotations

from pathlib import Path

import yaml

from techfeeds.validate import validate_registry

ROOT = Path(__file__).resolve().parents[1]


def test_registry_is_valid() -> None:
    assert validate_registry(ROOT) == []


def test_duplicate_feed_is_detected(tmp_path: Path) -> None:
    for directory in ("schema", "registry", "collections", "profiles", "sources/individuals"):
        (tmp_path / directory).mkdir(parents=True, exist_ok=True)

    for name in ("source.schema.json", "collection.schema.json", "profile.schema.json"):
        (tmp_path / "schema" / name).write_bytes((ROOT / "schema" / name).read_bytes())
    for name in ("topics.yaml", "traits.yaml", "languages.yaml"):
        (tmp_path / "registry" / name).write_bytes((ROOT / "registry" / name).read_bytes())

    base = {
        "schema_version": 1,
        "name": "Example",
        "kind": "individual",
        "language": "en",
        "website": "https://example.com/",
        "feeds": [
            {
                "url": "https://example.com/feed.xml",
                "format": "atom",
                "role": "primary",
                "official": True,
            }
        ],
        "topics": ["programming"],
        "traits": ["original"],
        "status": "active",
    }
    first = dict(base, id="one")
    second = dict(base, id="two", website="https://example.org/")
    (tmp_path / "sources/individuals/one.yaml").write_text(yaml.safe_dump(first), encoding="utf-8")
    (tmp_path / "sources/individuals/two.yaml").write_text(yaml.safe_dump(second), encoding="utf-8")

    errors = validate_registry(tmp_path)
    assert any("duplicate feed URL" in error for error in errors)


def test_collection_policy_is_enforced(tmp_path: Path) -> None:
    from shutil import copytree

    for name in ("sources", "collections", "profiles", "registry", "schema"):
        copytree(ROOT / name, tmp_path / name)

    target = tmp_path / "collections/essential.yaml"
    content = target.read_text(encoding="utf-8").replace("max_sources: 20", "max_sources: 1")
    target.write_text(content, encoding="utf-8")

    errors = validate_registry(tmp_path)
    assert any("exceeds policy max_sources=1" in error for error in errors)


def test_required_collection_rationale_is_enforced(tmp_path: Path) -> None:
    from shutil import copytree

    for name in ("sources", "collections", "profiles", "registry", "schema"):
        copytree(ROOT / name, tmp_path / name)

    target = tmp_path / "collections/essential.yaml"
    content = target.read_text(encoding="utf-8").replace(
        "  simon-willison: >-\n"
        "    High-frequency practitioner writing that connects AI, Python, databases, and the web "
        "with reproducible technical detail.\n",
        "",
    )
    target.write_text(content, encoding="utf-8")

    errors = validate_registry(tmp_path)
    assert any("missing selection rationale for simon-willison" in error for error in errors)
