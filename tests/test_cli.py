from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from techfeeds.cli import app


ROOT = Path(__file__).resolve().parents[1]
RUNNER = CliRunner()


def test_version() -> None:
    result = RUNNER.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.stdout


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
