from __future__ import annotations

from pathlib import Path
from shutil import copytree

from techfeeds.compile import compile_registry, generated_files_match

ROOT = Path(__file__).resolve().parents[1]


def test_compile_counts() -> None:
    payload = compile_registry(ROOT, write=False)
    assert payload["counts"] == {"sources": 50, "collections": 8, "profiles": 4}


def test_committed_generated_artifacts_are_current(tmp_path: Path) -> None:
    for name in ("sources", "collections", "profiles", "registry", "schema", "generated"):
        copytree(ROOT / name, tmp_path / name)
    assert generated_files_match(tmp_path)
