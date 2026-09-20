from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from techfeeds.cli import app

ROOT = Path(__file__).resolve().parents[1]
RUNNER = CliRunner()


def test_version() -> None:
    result = RUNNER.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "0.5.0" in result.stdout


def test_validate_compile_check_and_stats() -> None:
    root = str(ROOT)

    result = RUNNER.invoke(app, ["validate", "--root", root])
    assert result.exit_code == 0
    assert "registry valid" in result.stdout

    result = RUNNER.invoke(app, ["compile", "--root", root, "--check"])
    assert result.exit_code == 0
    assert "current" in result.stdout

    result = RUNNER.invoke(app, ["stats", "--root", root])
    assert result.exit_code == 0
    assert "50" in result.stdout


def test_compile_write_path(tmp_path: Path) -> None:
    from shutil import copytree

    for name in ("sources", "collections", "profiles", "registry", "schema"):
        copytree(ROOT / name, tmp_path / name)
    result = RUNNER.invoke(app, ["compile", "--root", str(tmp_path)])
    assert result.exit_code == 0
    assert "compiled" in result.stdout
    assert (tmp_path / "generated/registry.json").exists()


def test_validate_failure(tmp_path: Path) -> None:
    from shutil import copytree

    for name in ("sources", "collections", "profiles", "registry", "schema"):
        copytree(ROOT / name, tmp_path / name)
    target = tmp_path / "sources/individuals/simon-willison.yaml"
    content = target.read_text(encoding="utf-8").replace("language: en", "language: xx")
    target.write_text(content, encoding="utf-8")
    result = RUNNER.invoke(app, ["validate", "--root", str(tmp_path)])
    assert result.exit_code == 1
    assert "unknown language xx" in result.stdout


def test_probe_command(monkeypatch) -> None:
    async def fake_probe(root: Path, concurrency: int):
        assert root == ROOT
        assert concurrency == 3
        return {"counts": {"healthy": 2, "degraded": 1, "stale": 0, "broken": 0}}

    monkeypatch.setattr("techfeeds.cli.probe_registry", fake_probe)
    result = RUNNER.invoke(app, ["probe", "--root", str(ROOT), "--concurrency", "3"])
    assert result.exit_code == 0
    assert "healthy" in result.stdout
    assert "2" in result.stdout


def test_export_essential_as_json() -> None:
    result = RUNNER.invoke(
        app,
        ["export", "--root", str(ROOT), "--collection", "essential", "--format", "json"],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == 2
    assert payload["component_schema_versions"] == {"source": 2}
    assert payload["count"] == 18
    assert payload["sources"][0]["id"] == "simon-willison"
    assert payload["sources"][0]["curation"]["review_after"] == "2026-12-19"


def test_export_filters_are_and_composed() -> None:
    result = RUNNER.invoke(
        app,
        [
            "export",
            "--root",
            str(ROOT),
            "--topic",
            "security",
            "--trait",
            "independent",
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["count"] > 0
    assert all("security" in source["topics"] for source in payload["sources"])
    assert all("independent" in source["traits"] for source in payload["sources"])


def test_export_rejects_unknown_collection() -> None:
    result = RUNNER.invoke(
        app,
        ["export", "--root", str(ROOT), "--collection", "does-not-exist"],
    )
    assert result.exit_code == 2
    assert "unknown collection" in result.stdout


def test_export_writes_opml_file(tmp_path: Path) -> None:
    output = tmp_path / "security.opml"
    result = RUNNER.invoke(
        app,
        [
            "export",
            "--root",
            str(ROOT),
            "--topic",
            "security",
            "--format",
            "opml",
            "--output",
            str(output),
        ],
    )
    assert result.exit_code == 0
    content = output.read_text(encoding="utf-8")
    assert "<opml" in content
    assert 'techFeedsId="troy-hunt"' in content


def test_reviews_command_uses_explicit_as_of_date() -> None:
    result = RUNNER.invoke(app, ["reviews", "--root", str(ROOT), "--as-of", "2026-12-18"])
    assert result.exit_code == 0
    assert "no reviews due" in result.stdout

    result = RUNNER.invoke(app, ["reviews", "--root", str(ROOT), "--as-of", "2026-12-19"])
    assert result.exit_code == 0
    assert "simon-willison" in result.stdout
    assert "2026-12-19" in result.stdout


def test_reviews_command_rejects_invalid_date() -> None:
    result = RUNNER.invoke(app, ["reviews", "--root", str(ROOT), "--as-of", "not-a-date"])
    assert result.exit_code == 2
    assert "invalid --as-of date" in result.stdout


def test_query_command_emits_contract_v1_json() -> None:
    result = RUNNER.invoke(
        app,
        [
            "query",
            "--root",
            str(ROOT),
            "--collection",
            "essential",
            "--topic",
            "ai",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == 1
    assert payload["registry_schema_version"] == 2
    assert payload["query"] == {
        "schema_version": 1,
        "status": "active",
        "collection": "essential",
        "topics": ["ai"],
    }
    assert payload["count"] > 0


def test_query_command_consumes_compiled_registry_file() -> None:
    result = RUNNER.invoke(
        app,
        [
            "query",
            "--registry",
            str(ROOT / "generated/registry.json"),
            "--topic",
            "security",
            "--trait",
            "independent",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["count"] > 0
    assert all("security" in source["topics"] for source in payload["sources"])


def test_query_command_emits_machine_readable_error() -> None:
    result = RUNNER.invoke(
        app,
        ["query", "--registry", str(ROOT / "generated/registry.json"), "--topic", "nope"],
    )
    assert result.exit_code == 2
    payload = json.loads(result.stderr)
    assert payload["schema_version"] == 1
    assert payload["error"]["code"] == "unknown_filter_value"
    assert payload["error"]["field"] == "topic"



def test_profile_command_resolves_compiled_registry() -> None:
    result = RUNNER.invoke(
        app,
        [
            "profile",
            "researcher",
            "--registry",
            str(ROOT / "generated/registry.json"),
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == 1
    assert payload["profile"]["schema_version"] == 2
    assert payload["profile"]["id"] == "researcher"
    assert payload["budget"]["recommended_daily_items"] == 12
    ids = [item["source"]["id"] for item in payload["sources"]]
    assert "hacker-news" not in ids


def test_profile_command_writes_opml(tmp_path: Path) -> None:
    output = tmp_path / "developer.opml"
    result = RUNNER.invoke(
        app,
        [
            "profile",
            "developer",
            "--registry",
            str(ROOT / "generated/registry.json"),
            "--format",
            "opml",
            "--output",
            str(output),
        ],
    )
    assert result.exit_code == 0
    content = output.read_text(encoding="utf-8")
    assert "Awesome Tech Feeds — Profile: Developer" in content
    assert "techFeedsId=" in content


def test_profile_command_returns_machine_readable_unknown_profile_error() -> None:
    result = RUNNER.invoke(
        app,
        [
            "profile",
            "does-not-exist",
            "--registry",
            str(ROOT / "generated/registry.json"),
        ],
    )
    assert result.exit_code == 2
    payload = json.loads(result.stderr)
    assert payload["error"]["code"] == "unknown_filter_value"
    assert payload["error"]["field"] == "profile"
