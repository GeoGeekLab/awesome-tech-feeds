# Profile schema migration: v1 → v2

Profile v1 mixed a collection list, flat boost/exclude fields, and an ambiguous `recommended_daily_budget`. Profile v2 turns that configuration into an executable and testable policy.

## Field mapping

```text
v1 collections                 → v2 collections
v1 boost_topics                → v2 boost.topics
v1 exclude_traits              → v2 exclude.traits
v1 recommended_daily_budget    → v2 budget.recommended_daily_items
```

v2 additionally requires a human-readable `description` and explicit empty arrays for the other boost/exclude dimensions.

## Semantic changes

v1 did not define how multiple collections were merged, whether exclusions happened before boosts, how boost order affected source ordering, or whether daily budget truncated sources.

v2 defines all of those behaviors:

- collections are unioned in declared order;
- stable source ID deduplication keeps first appearance;
- only active sources resolve;
- exclusion happens before boost;
- each matched boost topic or trait contributes one priority point;
- ties retain first-appearance order;
- daily-item budget is metadata and does not truncate sources.

## Migration note: ai-engineer

The v1 `ai-engineer` profile contained `agents` in `boost_topics`, but no current selected source carries the `agents` topic. v2 semantic validation rejects dead boost rules, so that ineffective entry was removed rather than preserved.

## Compatibility

The compiled registry bundle remains contract v2, but its profile component version becomes 2:

```json
{
  "schema_version": 2,
  "component_schema_versions": {
    "source": 2,
    "collection": 1,
    "profile": 2
  }
}
```

The v0.5 SDK can still load older registry-v2 payloads containing profile component v1 for ordinary source queries. Calling `resolve_profile()` on such a payload fails explicitly with `RegistryCompatibilityError` instead of guessing legacy profile semantics.
