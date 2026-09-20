# Profiles 2.0

Profiles are explicit consumption policies over curated collections. They do not personalize from reader behavior and they do not assign source quality scores.

## Contract

Profile Contract v2 is published as:

- `schema/profile.v2.schema.json` — immutable v2 schema;
- `schema/profile.v1.schema.json` — immutable legacy schema;
- `schema/profile.schema.json` — latest alias, currently v2.

A v2 profile contains:

```yaml
schema_version: 2
id: researcher
name: Researcher
description: >-
  Research-focused AI and machine-learning sources emphasizing primary research and
  technical research explanations over community aggregation.
collections:
  - ai
boost:
  topics:
    - research
    - machine-learning
  traits: []
exclude:
  topics: []
  traits:
    - community
  sources: []
budget:
  recommended_daily_items: 12
```

## Resolution semantics

Resolution is deterministic and happens in this order:

1. walk `collections` in profile order;
2. union their source lists, deduplicating by stable source ID at first appearance;
3. keep active sources;
4. apply exclusions;
5. calculate boost priority;
6. sort by descending boost score, preserving first-appearance order for ties.

Exclusion has precedence over boost. A source matching any excluded source ID, topic, or trait is removed even if it would also match a boost.

The boost score is deliberately simple:

```text
priority_score =
    count(matched boost topics)
  + count(matched boost traits)
```

It is profile-specific priority metadata, not a global source-quality score.

## Budget semantics

`budget.recommended_daily_items` is a downstream article-processing or reading budget.

It does not truncate the resolved source set because the registry contains sources, not article arrival rates. A downstream reader can use the value when selecting articles after polling the resolved feeds.

## Validation

The registry rejects profile policy that is structurally valid but operationally meaningless:

- unknown collections, topics, traits, or excluded source IDs;
- excluded source IDs outside the profile's selected collections;
- the same topic or trait appearing in both boost and exclude;
- boost topics or traits that match no selected source;
- exclude topics or traits that match no selected source.

This is why the legacy `ai-engineer` `agents` boost was removed during migration: no current source in the registry carries the `agents` topic.

## SDK

```python
from techfeeds import Registry

registry = Registry.from_url()
result = registry.resolve_profile("researcher")

print(result.budget["recommended_daily_items"])
for item in result.sources:
    print(
        item.source.id,
        item.priority_score,
        item.matched_boost_topics,
        item.matched_boost_traits,
    )
```

`ProfileResult.to_json()` follows `schema/profile-result.v1.schema.json`. `ProfileResult.to_opml()` produces a feed-reader import preserving resolved profile order.

## CLI

```bash
techfeeds profile researcher --registry registry.json
techfeeds profile developer --registry registry.json --format opml -o developer.opml
```

## Generated artifacts

Each profile is compiled to two committed zero-server artifacts:

```text
generated/profile-ai-engineer.json
generated/profile-ai-engineer.opml
generated/profile-developer.json
generated/profile-developer.opml
generated/profile-founder.json
generated/profile-founder.opml
generated/profile-researcher.json
generated/profile-researcher.opml
```

The JSON artifacts preserve resolution metadata and explain why each source received its profile priority.
