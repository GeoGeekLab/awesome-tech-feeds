from __future__ import annotations

import json
from pathlib import Path

import yaml

from techfeeds.io import load_yaml
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
        "schema_version": 2,
        "name": "Example",
        "kind": "individual",
        "language": "en",
        "website": "https://example.com/",
        "description": (
            "Independent technical writing covering programming and software engineering."
        ),
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
        "curation": {
            "rationale": (
                "Admitted as a deterministic fixture for testing the source contract and "
                "registry validation behavior."
            ),
            "admission_basis": ["independent-analysis"],
            "reviewer": "tests",
            "reviewed_at": "2026-09-20",
            "review_after": "2026-12-19",
        },
        "provenance": {
            "added_by": "tests",
            "added_at": "2026-09-20",
            "evidence": [
                {"type": "identity", "url": "https://example.com/"},
                {"type": "feed", "url": "https://example.com/feed.xml"},
            ],
        },
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


def test_source_review_window_is_enforced(tmp_path: Path) -> None:
    from shutil import copytree

    for name in ("sources", "collections", "profiles", "registry", "schema"):
        copytree(ROOT / name, tmp_path / name)

    target = tmp_path / "sources/individuals/simon-willison.yaml"
    data = yaml.safe_load(target.read_text(encoding="utf-8"))
    data["curation"]["review_after"] = data["curation"]["reviewed_at"]
    target.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    errors = validate_registry(tmp_path)
    assert any("review_after must be 30 to 366 days after reviewed_at" in error for error in errors)


def test_source_provenance_must_track_identity_and_primary_feed(tmp_path: Path) -> None:
    from shutil import copytree

    for name in ("sources", "collections", "profiles", "registry", "schema"):
        copytree(ROOT / name, tmp_path / name)

    target = tmp_path / "sources/individuals/simon-willison.yaml"
    data = yaml.safe_load(target.read_text(encoding="utf-8"))
    data["provenance"]["evidence"][0]["url"] = "https://example.com/"
    data["provenance"]["evidence"][1]["url"] = "https://example.com/feed.xml"
    target.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    errors = validate_registry(tmp_path)
    assert any("canonical website as identity" in error for error in errors)
    assert any("primary feed URL" in error for error in errors)


def test_versioned_source_schemas_are_published() -> None:
    v1 = json.loads((ROOT / "schema/source.v1.schema.json").read_text(encoding="utf-8"))
    latest = json.loads((ROOT / "schema/source.schema.json").read_text(encoding="utf-8"))
    v2 = json.loads((ROOT / "schema/source.v2.schema.json").read_text(encoding="utf-8"))

    assert v1["properties"]["schema_version"]["const"] == 1
    assert latest["properties"]["schema_version"]["const"] == 2
    assert v2["properties"]["schema_version"]["const"] == 2
    latest.pop("$id")
    v2.pop("$id")
    assert latest == v2


def test_yaml_dates_remain_json_schema_strings(tmp_path: Path) -> None:
    target = tmp_path / "date.yaml"
    target.write_text(
        "reviewed_at: 2026-09-20\nactive: true\ncount: 2\n",
        encoding="utf-8",
    )

    data = load_yaml(target)
    assert data == {"reviewed_at": "2026-09-20", "active": True, "count": 2}


def test_profile_v2_rejects_dead_boost_policy(tmp_path: Path) -> None:
    from shutil import copytree

    for name in ("sources", "collections", "profiles", "registry", "schema"):
        copytree(ROOT / name, tmp_path / name)

    target = tmp_path / "profiles/ai-engineer.yaml"
    data = yaml.safe_load(target.read_text(encoding="utf-8"))
    data["boost"]["topics"].append("agents")
    target.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    errors = validate_registry(tmp_path)
    assert any("boost topic agents matches no selected source" in error for error in errors)


def test_versioned_profile_schemas_are_published() -> None:
    v1 = json.loads((ROOT / "schema/profile.v1.schema.json").read_text(encoding="utf-8"))
    latest = json.loads((ROOT / "schema/profile.schema.json").read_text(encoding="utf-8"))
    v2 = json.loads((ROOT / "schema/profile.v2.schema.json").read_text(encoding="utf-8"))

    assert v1["properties"]["schema_version"]["const"] == 1
    assert latest["properties"]["schema_version"]["const"] == 2
    assert v2["properties"]["schema_version"]["const"] == 2
    latest.pop("$id")
    v2.pop("$id")
    assert latest == v2
