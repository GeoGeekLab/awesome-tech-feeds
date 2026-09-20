# Geo Gecko v2 specification

Geo Gecko is a small terminal-dwelling gecko used as the visual signature for Awesome Tech Feeds.

## Recognition anchors

1. **Scanner eyes** — oversized dark pupils with blue highlights and tiny green status ticks.
2. **Terminal** — a dark GitHub-style panel with a green prompt and blue cursor/output line.
3. **RSS tail** — a curled blue tail that resolves into a feed signal.

Keep all three anchors on full-character artwork. The head mark may omit the terminal while retaining the eyes and feed signal.

## Shape language

- Flat vector geometry.
- Heavy dark outline for legibility on light and dark GitHub themes.
- Rounded terminal chrome and simple monospaced UI cues.
- Minimal gradients; use them only to add depth to the mint body or signal.
- No mandatory background on `core.svg` or `head.svg`.

## Palette

| Token | Value | Use |
| --- | --- | --- |
| `canvas` | `#0D1117` | terminal / GitHub-dark base |
| `panel` | `#161B22` | terminal chrome |
| `border` | `#30363D` | UI border |
| `text` | `#F0F6FC` | high-contrast foreground |
| `muted` | `#8B949E` | secondary UI detail |
| `mint` | `#B7F7E4` | gecko body |
| `blue` | `#58A6FF` | feed signal / scan highlight |
| `green` | `#39D353` | prompt / healthy accent |
| `amber` | `#D29922` | warning accent |
| `red` | `#FF7B72` | error accent |

## Small sizes

- `< 32 px`: use a generated icon from `head.svg`.
- `32–95 px`: use `head.svg`.
- `>= 96 px`: `core.svg` is preferred.
- Banner/README surfaces: use `hero.svg`.

## Variant rules

Operational states should change a signal, badge, or terminal detail rather than changing the character's personality. Profile variants may add a small accessory or label while preserving the base silhouette.

## File policy

`hero.svg`, `core.svg`, and `head.svg` are the canonical v2 sources. Raster exports are derivatives and should be regenerated from SVG when refreshed.
