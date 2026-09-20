# Geo Gecko

Geo Gecko is the project mascot for Awesome Tech Feeds.

The v2 art direction is intentionally flat and repo-native: GitHub-dark terminal chrome, mint gecko body, blue feed signal, and a literal `>_` prompt. It is designed to survive README rendering, issue comments, tiny icons, and SVG diffs without looking like a generic 3D character render.

## Canonical assets

- `hero.svg` — primary README/banner artwork.
- `core.svg` — full mascot with terminal and RSS tail.
- `head.svg` — compact mark for small surfaces.
- `tokens.json` — palette and construction tokens.
- `mascot-spec.md` — usage rules.

SVG is the source of truth. Existing raster and extended variant assets are retained for compatibility, but new project surfaces should start from the v2 SVG set above.

## Visual checksum

A full Geo Gecko should read as the same character even at a glance:

```text
scanner eyes + terminal prompt + RSS tail
```

Keep the silhouette friendly and technical. Prefer flat geometry and UI-like details over glossy rendering, photorealism, or decorative effects that disappear at small sizes.
