# Registry contract

The JSON Schemas in [`schema/`](../schema/) are the executable contract. This document explains the semantics that a schema alone cannot express.

## Source IDs

`id` is a permanent public identity.

- lowercase ASCII letters, digits, and hyphens;
- stable after merge;
- equal to the YAML filename;
- independent from current domain ownership or feed URL.

Do not rename an ID merely because branding or domains change.

## Kinds

Supported source kinds are:

- `individual`
- `company`
- `research`
- `community`
- `publication`
- `project`

Kind describes who publishes the source. It is not a quality tier.

## Feeds

Every active source must expose exactly one `primary` feed.

Additional feeds may be added with other roles when they represent a meaningful partition of the same source.

`official: true` means the endpoint is published or controlled by the source itself. A community-maintained bridge such as an RSSHub route should be marked `false` and, where appropriate, described as a fallback.

## Topics

Topics are controlled in [`registry/topics.yaml`](../registry/topics.yaml). They describe subject matter.

Do not use topics as praise, criticism, audience level, or publishing frequency.

## Traits

Traits are controlled in [`registry/traits.yaml`](../registry/traits.yaml). They describe recurring properties such as `deep-dive`, `practitioner`, `independent`, or `company-engineering`.

Avoid subjective superlatives such as `best`, `excellent`, or `must-read`.

## Status

`active` means the registry currently expects the source to be consumable.

`retired` preserves historical identity when the source has intentionally ended, merged, or moved to a replacement identity. Retirement is an editorial decision; a transient failed probe is not sufficient evidence.

## Collections

Collections are curated bundles of source IDs. They can express a narrower editorial point of view than the source records themselves.

A source may belong to multiple collections.

## Profiles

Profiles combine collections and optional topic preferences for common reader roles. They are starting points, not personalized ranking models.
