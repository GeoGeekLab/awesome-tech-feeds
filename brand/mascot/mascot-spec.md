# Geo Gecko mascot specification

Geo Gecko is the cartoon mascot for Awesome Tech Feeds.

The design goal is closer to a comic pet than a product logo: recognizable silhouette, oversized expressive face, compact body, and simple props.

## Character proportions

- Head is intentionally oversized: roughly half the visual mass of the full character.
- Body is short and rounded.
- Arms and feet are small, soft, and secondary.
- Eyes use large pupils, strong white highlights, and a small blue reflected highlight.
- Rosy cheeks and a small open smile provide the default friendly expression.
- Three tiny head bumps keep the silhouette reptilian without making the character spiky or aggressive.

## Recognition anchors

1. **Mint gecko** — round mint head/body with dark ink outline.
2. **Sparkling eyes** — two oversized eyes with white + blue highlights.
3. **Blue curled tail** — the tail doubles as the feed/RSS signature.

The laptop is a prop, not an identity anchor.

## Shape language

- Cartoon/chibi proportions.
- Thick rounded outline.
- Soft curves; avoid hard mechanical geometry on the character itself.
- Minimal detail at small sizes.
- Technical motifs belong in props or the surrounding composition.
- No photorealistic, glossy 3D, cyberpunk, robotic, or mascot-suit styling.

## Palette

| Token | Value | Use |
| --- | --- | --- |
| `ink` | `#17212B` | character outline / pupils |
| `mint-light` | `#CFFCEB` | head highlight |
| `mint` | `#8DE6C7` | body |
| `mint-mid` | `#9AEACF` | limbs / bumps |
| `spot` | `#65C6A8` | facial spots |
| `cream` | `#FFFDF3` | belly |
| `blue` | `#79C0FF` | eye highlight / feed signal |
| `blue-strong` | `#388BFD` | tail |
| `pink` | `#FFB3C1` | cheeks |
| `mouth` | `#FF8FA3` | smile |
| `panel` | `#24292F` | laptop / GitHub props |

## Small sizes

- `< 32 px`: generated icon from `head.svg`.
- `32–95 px`: use `head.svg`.
- `>= 96 px`: use `core.svg`.
- README/banner surfaces: use `hero.svg`.

At small sizes, preserve the face before preserving props.

## Variant rules

Operational states should alter a small badge, tail signal, expression, or accessory. Do not deform the base face or turn failure states into injury/sickness.

Profile variants may change a tiny accessory while keeping the same head, eye proportions, body silhouette, and tail.

## File policy

`hero.svg`, `core.svg`, and `head.svg` are the canonical sources. Raster exports are derivatives and should be regenerated when the canonical SVG changes.
