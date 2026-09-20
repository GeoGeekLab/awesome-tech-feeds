from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry as SchemaRegistry
from referencing import Resource

from techfeeds.consumer import (
    ConsumerError,
    Query,
    QueryContractError,
    Registry,
    RegistryCompatibilityError,
    RegistryIntegrityError,
    UnknownFilterValueError,
)

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "generated/registry.json"


def test_query_is_canonical_and_round_trips() -> None:
    query = Query(
        topics=("security", "ai", "security"),
        traits=("independent", "deep-dive", "independent"),
        status="active",
    )
    assert query.topics == ("ai", "security")
    assert query.traits == ("deep-dive", "independent")
    assert Query.from_dict(query.to_dict()) == query


def test_query_contract_rejects_unknown_fields_and_versions() -> None:
    with pytest.raises(QueryContractError):
        Query.from_dict({"schema_version": 1, "status": "active", "surprise": True})
    with pytest.raises(QueryContractError):
        Query.from_dict({"schema_version": 99, "status": "active"})


def test_registry_loads_compiled_artifact_and_queries_collection() -> None:
    registry = Registry.from_file(REGISTRY_PATH)
    result = registry.query(Query(collection="essential"))

    assert registry.schema_version == 2
    assert registry.component_schema_versions["source"] == 2
    assert "essential" in registry.collections
    assert result.count == 18
    assert result.sources[0].id == "simon-willison"
    assert result.to_dict()["query"] == {
        "schema_version": 1,
        "status": "active",
        "collection": "essential",
    }


def test_query_filters_are_all_of_and_cross_dimension() -> None:
    registry = Registry.from_file(REGISTRY_PATH)
    result = registry.query(Query(topics=("security",), traits=("independent",), language="en"))

    assert result.count > 0
    for source in result.sources:
        assert "security" in source["topics"]
        assert "independent" in source["traits"]
        assert source["language"] == "en"


def test_non_collection_query_order_is_source_id() -> None:
    registry = Registry.from_file(REGISTRY_PATH)
    result = registry.query(Query())
    ids = [source.id for source in result.sources]
    assert ids == sorted(ids)


def test_unknown_filter_error_is_machine_readable() -> None:
    registry = Registry.from_file(REGISTRY_PATH)

    with pytest.raises(UnknownFilterValueError) as captured:
        registry.query(Query(topics=("does-not-exist",)))

    error = captured.value
    payload = error.to_dict()
    assert isinstance(error, ValueError)
    assert isinstance(error, ConsumerError)
    assert payload["schema_version"] == 1
    assert payload["error"]["code"] == "unknown_filter_value"
    assert payload["error"]["field"] == "topic"
    assert payload["error"]["value"] == "does-not-exist"
    assert "security" in payload["error"]["choices"]


def test_result_serializers_are_deterministic() -> None:
    registry = Registry.from_file(REGISTRY_PATH)
    result = registry.query(Query(collection="essential", topics=("ai",)))

    payload = json.loads(result.to_json())
    assert payload["schema_version"] == 1
    assert payload["registry_schema_version"] == 2
    assert payload["component_schema_versions"]["source"] == 2
    assert payload["count"] == result.count

    opml = result.to_opml()
    assert "<opml" in opml
    assert "Awesome Tech Feeds — essential" in opml
    for source in result.sources:
        assert f'techFeedsId="{source.id}"' in opml


def test_source_record_does_not_leak_mutable_registry_state() -> None:
    registry = Registry.from_file(REGISTRY_PATH)
    source = registry.get("simon-willison")
    assert source is not None

    topics = source["topics"]
    topics.append("mutated")

    same_source = registry.get("simon-willison")
    assert same_source is not None
    assert "mutated" not in same_source["topics"]


def test_registry_integrity_check(tmp_path: Path) -> None:
    raw = REGISTRY_PATH.read_bytes()
    target = tmp_path / "registry.json"
    target.write_bytes(raw)
    expected = hashlib.sha256(raw).hexdigest()

    registry = Registry.from_file(target, expected_sha256=expected)
    assert registry.schema_version == 2

    with pytest.raises(RegistryIntegrityError):
        Registry.from_file(target, expected_sha256="0" * 64)


def test_registry_contract_version_is_checked() -> None:
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    payload["schema_version"] = 99

    with pytest.raises(RegistryCompatibilityError) as captured:
        Registry.from_mapping(payload)

    assert captured.value.to_dict()["error"]["component"] == "registry"


def test_registry_from_url_uses_downloaded_bytes(monkeypatch: pytest.MonkeyPatch) -> None:
    raw = REGISTRY_PATH.read_bytes()

    class FakeResponse:
        content = raw

        def raise_for_status(self) -> None:
            return None

    def fake_get(url: str, *, follow_redirects: bool, timeout: float) -> FakeResponse:
        assert url == "https://example.test/registry.json"
        assert follow_redirects is True
        assert timeout == 4.0
        return FakeResponse()

    monkeypatch.setattr("techfeeds.consumer.httpx.get", fake_get)
    registry = Registry.from_url("https://example.test/registry.json", timeout=4.0)
    assert registry.get("simon-willison") is not None


def test_serialized_query_contracts_validate_against_published_schemas() -> None:
    query_schema = json.loads((ROOT / "schema/query.v1.schema.json").read_text(encoding="utf-8"))
    result_schema = json.loads(
        (ROOT / "schema/query-result.v1.schema.json").read_text(encoding="utf-8")
    )
    error_schema = json.loads(
        (ROOT / "schema/query-error.v1.schema.json").read_text(encoding="utf-8")
    )
    schema_registry = SchemaRegistry().with_resource(
        query_schema["$id"],
        Resource.from_contents(query_schema),
    )

    registry = Registry.from_file(REGISTRY_PATH)
    result = registry.query(Query(collection="essential", topics=("ai",)))

    Draft202012Validator(query_schema).validate(result.query.to_dict())
    Draft202012Validator(result_schema, registry=schema_registry).validate(result.to_dict())

    with pytest.raises(UnknownFilterValueError) as captured:
        registry.query(Query(topics=("not-a-topic",)))
    Draft202012Validator(error_schema).validate(captured.value.to_dict())



def test_profile_v2_resolution_is_explainable_and_budget_does_not_truncate() -> None:
    registry = Registry.from_file(REGISTRY_PATH)
    result = registry.resolve_profile("founder")

    assert registry.component_schema_versions["profile"] == 2
    assert "founder" in registry.profiles
    assert result.profile.id == "founder"
    assert result.budget["recommended_daily_items"] == 10
    assert result.count > result.budget["recommended_daily_items"]
    assert result.candidate_count >= result.count
    assert result.excluded_count > 0

    ids = [item.source.id for item in result.sources]
    assert "openai-news" not in ids
    assert "kubernetes-blog" not in ids
    scores = [item.priority_score for item in result.sources]
    assert scores == sorted(scores, reverse=True)


def test_profile_exclusion_precedes_boost() -> None:
    registry = Registry.from_file(REGISTRY_PATH)
    result = registry.resolve_profile("researcher")
    ids = [item.source.id for item in result.sources]

    assert "hacker-news" not in ids
    assert result.excluded_count == 1
    assert any("research" in item.matched_boost_topics for item in result.sources)


def test_unknown_profile_is_machine_readable() -> None:
    registry = Registry.from_file(REGISTRY_PATH)
    with pytest.raises(UnknownFilterValueError) as captured:
        registry.resolve_profile("does-not-exist")
    assert captured.value.to_dict()["error"]["field"] == "profile"


def test_profile_result_matches_published_schema() -> None:
    schema = json.loads(
        (ROOT / "schema/profile-result.v1.schema.json").read_text(encoding="utf-8")
    )
    registry = Registry.from_file(REGISTRY_PATH)
    result = registry.resolve_profile("developer")
    Draft202012Validator(schema).validate(result.to_dict())

    opml = result.to_opml()
    assert "Awesome Tech Feeds — Profile: Developer" in opml
    assert f'techFeedsId="{result.sources[0].source.id}"' in opml
