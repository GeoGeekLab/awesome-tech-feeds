# Consumer SDK and Query Contract

Version 0.5 keeps the compiled registry a stable consumer surface rather than requiring downstream code to understand repository YAML layout.

## Public Python API

The supported public imports are:

```python
from techfeeds import (
    DEFAULT_REGISTRY_URL,
    ConsumerError,
    Query,
    QueryContractError,
    QueryResult,
    ProfileRecord,
    ProfileResult,
    ProfileSource,
    Registry,
    RegistryCompatibilityError,
    RegistryIntegrityError,
    RegistryLoadError,
    SourceRecord,
    UnknownFilterValueError,
)
```

Modules and functions not re-exported from `techfeeds` remain implementation details unless another document explicitly marks them public.

## Loading a registry

The SDK consumes the compiled full `registry.json`.

```python
from techfeeds import Registry

registry = Registry.from_file("registry.json")
```

It can also load the latest GitHub release:

```python
registry = Registry.from_url()
```

For pinned supply-chain workflows, verify bytes before parsing:

```python
registry = Registry.from_file(
    "registry.json",
    expected_sha256="<sha256 from SHA256SUMS>",
)
```

The same `expected_sha256` option is available for `from_url`.

The v0.5 SDK supports compiled registry contract v2, source contract v2, and executable profile contract v2. It can still load a registry-v2 payload with profile component v1 for ordinary queries; profile resolution requires profile v2. Unsupported contract versions fail explicitly with `RegistryCompatibilityError`; the SDK does not guess at forward compatibility.

## Query request v1

A query is immutable and canonicalized.

```python
from techfeeds import Query

query = Query(
    collection="essential",
    topics=("ai", "llm"),
    traits=("research",),
    language="en",
    status="active",
)
```

Its machine representation follows `schema/query.v1.schema.json`:

```json
{
  "schema_version": 1,
  "collection": "essential",
  "topics": ["ai", "llm"],
  "traits": ["research"],
  "language": "en",
  "status": "active"
}
```

Topics and traits are set-like inputs. The SDK removes duplicates and sorts them before serialization so equivalent queries have identical representations.

## Filter semantics

All dimensions compose with logical AND.

```text
collection membership
AND all requested topics
AND all requested traits
AND language, when supplied
AND kind, when supplied
AND status
```

Within `topics` and `traits`, every requested value is required. There is deliberately no implicit OR mode in query contract v1.

`status` is one of `active`, `retired`, or `all`; it defaults to `active`.

A collection narrows the candidate set before the remaining filters are applied.

## Ordering contract

Ordering is deterministic:

- collection queries preserve the collection's declared source order;
- non-collection queries are ordered lexicographically by stable source ID;
- filtering never re-ranks sources.

This is an ordering guarantee, not a quality ranking.

## Result contract v1

```python
result = registry.query(query)

print(result.count)
print(result.sources[0].id)
print(result.to_json())
print(result.to_opml())
```

JSON follows `schema/query-result.v1.schema.json`:

```json
{
  "schema_version": 1,
  "registry_schema_version": 2,
  "component_schema_versions": {
    "source": 2,
    "collection": 1,
    "profile": 1
  },
  "query": {
    "schema_version": 1,
    "status": "active"
  },
  "count": 50,
  "sources": []
}
```

`SourceRecord` is a read-only mapping facade. Values returned from it are defensive copies; mutating a returned list or dictionary does not mutate registry state.

## Error contract v1

Consumer errors expose stable machine-readable codes through `to_dict()` and `to_json()`.

```json
{
  "schema_version": 1,
  "error": {
    "code": "unknown_filter_value",
    "message": "unknown topic: does-not-exist",
    "field": "topic",
    "value": "does-not-exist",
    "choices": ["ai", "databases", "security"]
  }
}
```

The stable v1 codes are:

- `registry_load_error`
- `registry_integrity_error`
- `unsupported_registry_contract`
- `invalid_query_contract`
- `unknown_filter_value`

Applications should branch on `code`, not parse human-readable `message`.

## CLI query surface

The CLI uses the same SDK implementation.

Query the repository registry:

```bash
techfeeds query --root . --collection essential --topic ai
```

Query a downloaded compiled registry without a repository checkout:

```bash
techfeeds query --registry registry.json --topic security --trait independent
```

Successful output is Query Result Contract v1 JSON. Query failures are emitted as Query Error Contract v1 JSON on stderr with exit code 2.

The older `techfeeds export` command remains available and preserves its existing JSON/OPML output shape for compatibility, but its filtering is delegated to the same SDK query engine.

## Compatibility policy

Query request/result/error contract v1 is independent of registry contract v2.

A future additive SDK release may add optional Python helpers without changing query contract v1. Adding required fields, changing filter meaning, changing deterministic ordering, or changing error-code semantics requires a new query contract version.

Versioned query schemas are immutable after release. The unversioned source schema alias does not apply to query schemas; consumers should reference the explicit v1 filenames.


## Profile resolution

Profiles use a separate contract from ad hoc Query Contract v1.

```python
result = registry.resolve_profile("founder")
```

The returned `ProfileResult` contains the Profile Contract v2 policy, downstream daily-item budget, candidate/exclusion counts, and ordered `ProfileSource` entries.

Each `ProfileSource` exposes the full `SourceRecord`, a deterministic `priority_score`, and the exact boost topics/traits that matched. This is explainability for one profile policy, not a global ranking.

Profile Result Contract v1 is published as `schema/profile-result.v1.schema.json`. See [`profiles.md`](profiles.md) for the full resolution algorithm.
