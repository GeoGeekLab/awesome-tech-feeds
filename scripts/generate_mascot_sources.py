# Geo Gecko canonical variant generator. Keep outputs deterministic.
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASCOT = ROOT / "brand" / "mascot"


def core_with(label: str, overlay: str) -> str:
    core = (MASCOT / "core.svg").read_text(encoding="utf-8")
    core = core.replace(
        'aria-label="Geo Gecko core mascot"',
        f'aria-label="Geo Gecko {label}"',
        1,
    )
    return core.replace("</svg>", overlay + "</svg>")


def write(rel: str, content: str) -> None:
    path = MASCOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def badge(color: str, symbol: str, x: int = 392, y: int = 105) -> str:
    return (
        f'<g transform="translate({x} {y})">'
        f'<circle r="42" fill="{color}" stroke="#0F172A" stroke-width="8"/>'
        f'<text x="0" y="13" text-anchor="middle" font-family="sans-serif" '
        f'font-size="42" font-weight="700" fill="#FFFFFF">{symbol}</text></g>'
    )


def panel(title: str, body: str, color: str = "#0B1F3A") -> str:
    return (
        '<g transform="translate(147 294)">'
        f'<rect width="218" height="112" rx="18" fill="{color}" '
        'stroke="#0F172A" stroke-width="8"/>'
        f'<text x="109" y="43" text-anchor="middle" font-family="monospace" '
        f'font-size="24" font-weight="700" fill="#FFFFFF">{title}</text>'
        f'<text x="109" y="78" text-anchor="middle" font-family="sans-serif" '
        f'font-size="17" fill="#E2E8F0">{body}</text></g>'
    )


def generate_states() -> None:
    write("states/healthy.svg", core_with("healthy", badge("#10B981", "✓")))
    write("states/degraded.svg", core_with("degraded", badge("#F59E0B", "!", 400, 112)))
    stale = (
        '<g font-family="sans-serif" font-weight="700" fill="#64748B">'
        '<text x="365" y="92" font-size="34">Z</text>'
        '<text x="402" y="62" font-size="28">Z</text>'
        '<text x="430" y="38" font-size="22">Z</text></g>'
    )
    write("states/stale.svg", core_with("stale", stale))
    broken = (
        '<g transform="translate(395 110)" stroke="#EF4444" stroke-width="13" '
        'stroke-linecap="round"><circle r="42" fill="#FFFFFF" stroke="#0F172A" '
        'stroke-width="8"/><path d="M-14 -14 L14 14 M14 -14 L-14 14"/></g>'
        '<path d="M411 312 l24 -18" stroke="#EF4444" stroke-width="12" '
        'stroke-linecap="round"/>'
    )
    write("states/broken.svg", core_with("broken", broken))


def generate_profiles() -> None:
    developer = panel("&lt;/&gt;", "Developer", "#0B1F3A")
    write("profiles/developer.svg", core_with("developer profile", developer))

    ai = (
        '<g transform="translate(382 92)" stroke="#8B5CF6" stroke-width="7">'
        '<line x1="0" y1="0" x2="-42" y2="35"/><line x1="0" y1="0" x2="40" y2="38"/>'
        '<line x1="-42" y1="35" x2="8" y2="68"/>'
        '<circle cx="0" cy="0" r="14" fill="#8B5CF6"/>'
        '<circle cx="-42" cy="35" r="12" fill="#38BDF8"/>'
        '<circle cx="40" cy="38" r="12" fill="#38BDF8"/>'
        '<circle cx="8" cy="68" r="12" fill="#2563EB"/></g>'
    )
    write("profiles/ai-engineer.svg", core_with("AI engineer profile", ai))

    founder = (
        '<g transform="translate(256 346)">'
        '<circle r="72" fill="#FFFFFF" stroke="#0F172A" stroke-width="9"/>'
        '<circle r="58" fill="none" stroke="#F59E0B" stroke-width="8"/>'
        '<path d="M-18 28 L12 -32 L27 23 L-12 37 Z" fill="#2563EB" '
        'stroke="#0F172A" stroke-width="5"/></g>'
    )
    write("profiles/founder.svg", core_with("founder profile", founder))

    researcher = (
        '<g transform="translate(312 315)">'
        '<circle cx="0" cy="0" r="52" fill="#E0F2FE" fill-opacity=".72" '
        'stroke="#0F172A" stroke-width="9"/>'
        '<circle cx="0" cy="0" r="38" fill="none" stroke="#38BDF8" stroke-width="6"/>'
        '<path d="M38 38 L83 83" stroke="#0F172A" stroke-width="18" '
        'stroke-linecap="round"/></g>'
    )
    write("profiles/researcher.svg", core_with("researcher profile", researcher))


def generate_stickers() -> None:
    write("stickers/verified.svg", core_with("verified sticker", badge("#10B981", "✓")))
    feed = (
        '<g transform="translate(390 105)">'
        '<circle r="46" fill="#F59E0B" stroke="#0F172A" stroke-width="8"/>'
        '<circle cx="-17" cy="17" r="7" fill="#FFFFFF"/>'
        '<path d="M-17 -5 A22 22 0 0 1 5 17 M-17 -28 A45 45 0 0 1 28 17" '
        'fill="none" stroke="#FFFFFF" stroke-width="9" stroke-linecap="round"/></g>'
    )
    write("stickers/feed-found.svg", core_with("feed found sticker", feed))
    no_noise = (
        '<g transform="translate(392 110)">'
        '<circle r="47" fill="#FFFFFF" stroke="#EF4444" stroke-width="10"/>'
        '<path d="M-31 -31 L31 31" stroke="#EF4444" stroke-width="12" '
        'stroke-linecap="round"/>'
        '<path d="M-18 0 C-5 -18 5 18 18 0" fill="none" stroke="#0F172A" '
        'stroke-width="8"/></g>'
    )
    write("stickers/no-noise.svg", core_with("no noise sticker", no_noise))
    curious = (
        '<g transform="translate(360 76)">'
        '<path d="M0 60 C0 20 75 20 75 60" fill="#38BDF8" '
        'stroke="#0F172A" stroke-width="8"/>'
        '<path d="M15 60 L-2 92 M60 60 L78 92" stroke="#0F172A" '
        'stroke-width="13" stroke-linecap="round"/></g>'
    )
    write("stickers/stay-curious.svg", core_with("stay curious sticker", curious))


def core_inner() -> str:
    core = (MASCOT / "core.svg").read_text(encoding="utf-8")
    return core.split(">", 1)[1].rsplit("</svg>", 1)[0]


def generate_social() -> None:
    inner = core_inner()
    avatar = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" '
        'role="img" aria-label="Geo Gecko GitHub avatar">'
        '<circle cx="256" cy="256" r="250" fill="#E0F2FE"/>'
        '<circle cx="256" cy="256" r="238" fill="none" stroke="#2563EB" stroke-width="12"/>'
        f'<g transform="translate(26 28) scale(.9)">{inner}</g></svg>'
    )
    write("social/github-avatar.svg", avatar)

    card = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630" '
        'role="img" aria-label="Geo Gecko social card">'
        '<defs><linearGradient id="bg" x1="0" x2="1"><stop stop-color="#0B1F3A"/>'
        '<stop offset="1" stop-color="#2563EB"/></linearGradient></defs>'
        '<rect width="1200" height="630" rx="36" fill="url(#bg)"/>'
        f'<g transform="translate(10 45) scale(1.0)">{inner}</g>'
        '<text x="590" y="230" font-family="sans-serif" font-size="66" '
        'font-weight="700" fill="#FFFFFF">Awesome Tech Feeds</text>'
        '<text x="594" y="305" font-family="sans-serif" font-size="36" '
        'fill="#BAE6FD">Curate the source. Verify the feed.</text>'
        '<text x="594" y="410" font-family="sans-serif" font-size="28" '
        'fill="#E2E8F0">Geo Gecko · GeoGeekLab</text></svg>'
    )
    write("social/social-card.svg", card)


def generate_spec() -> None:
    colors = [
        ("Brand blue", "#2563EB"),
        ("Signal", "#38BDF8"),
        ("Healthy", "#10B981"),
        ("Degraded", "#F59E0B"),
        ("Broken", "#EF4444"),
        ("AI accent", "#8B5CF6"),
        ("Neutral", "#64748B"),
    ]
    items = []
    for i, (label, color) in enumerate(colors):
        x = 90 + i * 155
        items.append(
            f'<circle cx="{x}" cy="140" r="48" fill="{color}"/>'
            f'<text x="{x}" y="220" text-anchor="middle" font-family="sans-serif" '
            f'font-size="19" font-weight="700" fill="#0F172A">{label}</text>'
            f'<text x="{x}" y="250" text-anchor="middle" font-family="monospace" '
            f'font-size="17" fill="#64748B">{color}</text>'
        )
    palette = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 360">'
        '<rect width="1200" height="360" fill="#F8FAFC"/>'
        '<text x="60" y="65" font-family="sans-serif" font-size="34" '
        'font-weight="700" fill="#0F172A">Geo Gecko Color System</text>' + "".join(items) + "</svg>"
    )
    write("spec/palette.svg", palette)

    inner = core_inner()
    construction = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 900">'
        '<rect width="900" height="900" fill="#F8FAFC"/>'
        '<g opacity=".28" stroke="#2563EB" stroke-width="3" stroke-dasharray="12 12">'
        '<line x1="450" y1="70" x2="450" y2="830"/>'
        '<line x1="90" y1="450" x2="810" y2="450"/>'
        '<circle cx="450" cy="450" r="350" fill="none"/>'
        '<circle cx="450" cy="450" r="250" fill="none"/></g>'
        f'<g transform="translate(194 194)">{inner}</g>'
        '<text x="50" y="70" font-family="sans-serif" font-size="34" '
        'font-weight="700" fill="#0F172A">Geo Gecko Construction</text></svg>'
    )
    write("spec/construction.svg", construction)


def main() -> None:
    generate_states()
    generate_profiles()
    generate_stickers()
    generate_social()
    generate_spec()


if __name__ == "__main__":
    main()
