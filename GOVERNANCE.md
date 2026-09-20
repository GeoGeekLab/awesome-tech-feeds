# Governance

Awesome Tech Feeds uses lightweight maintainer review rather than numerical voting or automated quality scoring.

## Responsibilities

Maintainers are responsible for:

- preserving source identity and schema stability;
- reviewing whether additions provide durable technical signal and recording an explicit source-level rationale;
- keeping controlled vocabularies coherent;
- distinguishing temporary endpoint failures from editorial retirement;
- resolving duplicate or overlapping identities conservatively;
- keeping provenance evidence aligned with canonical identity and primary feeds;
- scheduling and performing periodic source reviews;
- keeping generated artifacts reproducible.

## Editorial decisions

Admission is qualitative by design. The repository does not publish a global score for authors, companies, or publications.

A maintainer should be able to explain an inclusion or exclusion in terms of source characteristics, coverage, originality, and registry scope rather than personal prestige.

Every admitted source records the responsible reviewer, review dates, admission basis, and provenance. These records make a qualitative decision auditable without pretending it is an objective numerical score.

Collections may encode an attention budget and require collection-specific rationales. A rationale explains why a source belongs in that bundle; it is not a global score for the source. Maintainers should prefer replacement over unbounded growth when a capped collection already covers a domain adequately.

## Automation boundary

Automation may validate syntax, references, duplicates, feeds, redirects, and generated artifacts.

Automation may suggest metadata.

Automation does not make the final decision to admit or remove a source.
