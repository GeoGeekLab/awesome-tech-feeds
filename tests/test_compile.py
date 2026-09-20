from __future__ import annotations

from pathlib import Path
from shutil import copytree

from techfeeds.compile import compile_registry, generated_files_match

ROOT = Path(__file__).resolve().parents[1]


def test_compile_counts() -> None:
    payload = compile_registry(ROOT, write=False)
    assert payload["schema_version"] == 2
    assert payload["component_schema_versions"] == {"source": 2, "collection": 1, "profile": 2}
    assert payload["counts"] == {"sources": 50, "collections": 8, "profiles": 4}
    assert all(source["schema_version"] == 2 for source in payload["sources"])
    assert all("curation" in source and "provenance" in source for source in payload["sources"])
    assert all(profile["schema_version"] == 2 for profile in payload["profiles"])
    essential = next(item for item in payload["collections"] if item["id"] == "essential")
    assert len(essential["sources"]) == 18
    assert essential["policy"]["max_sources"] == 20
    assert set(essential["selection_rationale"]) == set(essential["sources"])


def test_committed_generated_artifacts_are_current(tmp_path: Path) -> None:
    for name in ("sources", "collections", "profiles", "registry", "schema", "generated"):
        copytree(ROOT / name, tmp_path / name)
    assert generated_files_match(tmp_path)



def test_profile_artifacts_are_compiled() -> None:
    for profile_id in ("ai-engineer", "developer", "founder", "researcher"):
        json_path = ROOT / "generated" / f"profile-{profile_id}.json"
        opml_path = ROOT / "generated" / f"profile-{profile_id}.opml"
        assert json_path.exists()
        assert opml_path.exists()
