from __future__ import annotations

from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree

import cairosvg
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
MASCOT = ROOT / "brand" / "mascot"


def viewbox(path: Path) -> tuple[float, float]:
    root = ElementTree.parse(path).getroot()
    raw = root.attrib.get("viewBox", "0 0 512 512").split()
    return float(raw[2]), float(raw[3])


def raster(
    path: Path,
    *,
    width: int,
    height: int | None = None,
    square: bool = False,
) -> Image.Image:
    vbw, vbh = viewbox(path)
    if square:
        side = width
        scale = min(side / vbw, side / vbh)
        rw = max(1, round(vbw * scale))
        rh = max(1, round(vbh * scale))
        raw = cairosvg.svg2png(url=str(path), output_width=rw, output_height=rh)
        image = Image.open(BytesIO(raw)).convert("RGBA")
        canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        canvas.alpha_composite(image, ((side - rw) // 2, (side - rh) // 2))
        return canvas

    target_height = height or max(1, round(width * vbh / vbw))
    raw = cairosvg.svg2png(
        url=str(path),
        output_width=width,
        output_height=target_height,
    )
    return Image.open(BytesIO(raw)).convert("RGBA")


def save_png(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG", optimize=True)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    candidates = [
        Path("/usr/share/fonts/truetype/dejavu") / name,
        Path("/usr/share/fonts/dejavu") / name,
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def fit(image: Image.Image, box: tuple[int, int]) -> Image.Image:
    copy = image.copy()
    copy.thumbnail(box, Image.Resampling.LANCZOS)
    return copy


def contact_sheet() -> None:
    assets = [
        ("Core", MASCOT / "core.png"),
        ("Head", MASCOT / "head.png"),
        *[
            (f"State · {name.title()}", MASCOT / "states" / f"{name}.png")
            for name in (
                "idle",
                "scanning",
                "verified",
                "fetching",
                "thinking",
                "healthy",
                "degraded",
                "stale",
                "broken",
            )
        ],
        *[
            (
                f"Profile · {name.replace('-', ' ').title()}",
                MASCOT / "profiles" / f"{name}.png",
            )
            for name in ("developer", "ai-engineer", "founder", "researcher")
        ],
        *[
            (
                f"Sticker · {name.replace('-', ' ').title()}",
                MASCOT / "stickers" / f"{name}.png",
            )
            for name in ("verified", "feed-found", "no-noise", "stay-curious")
        ],
        ("GitHub avatar", MASCOT / "social" / "github-avatar.png"),
        ("Social card", MASCOT / "social" / "social-card.png"),
        ("Palette", MASCOT / "spec" / "palette.png"),
        ("Construction", MASCOT / "spec" / "construction.png"),
    ]
    sheet = Image.new("RGB", (1120, 1500), "#F8FAFC")
    draw = ImageDraw.Draw(sheet)
    draw.text(
        (48, 32),
        "Geo Gecko · Production Asset Sheet",
        fill="#0F172A",
        font=font(34, True),
    )
    draw.text(
        (48, 78),
        "Canonical SVG sources + generated raster exports",
        fill="#64748B",
        font=font(18),
    )
    cols, cell_w, cell_h = 4, 260, 218
    x0, y0 = 40, 120
    for index, (label, path) in enumerate(assets):
        row, col = divmod(index, cols)
        x = x0 + col * cell_w
        y = y0 + row * cell_h
        draw.rounded_rectangle(
            (x, y, x + 240, y + 198),
            18,
            fill="white",
            outline="#E2E8F0",
            width=2,
        )
        image = fit(Image.open(path).convert("RGBA"), (170, 145))
        sheet.paste(image, (x + (240 - image.width) // 2, y + 10), image)
        draw.text((x + 12, y + 164), label, fill="#0F172A", font=font(14, True))

    out = MASCOT / "previews" / "production-contact-sheet.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, optimize=True)


def brand_board() -> None:
    board = Image.new("RGBA", (1536, 1024), "#F8FAFC")
    draw = ImageDraw.Draw(board)
    draw.text((56, 48), "Geo Gecko", fill="#0F172A", font=font(58, True))
    draw.text(
        (58, 116),
        "Curate the source. Verify the feed.",
        fill="#475569",
        font=font(24),
    )

    core = fit(Image.open(MASCOT / "core.png").convert("RGBA"), (430, 430))
    board.alpha_composite(core, (58, 180))
    draw.text(
        (58, 650),
        "Recognition anchors",
        fill="#0F172A",
        font=font(24, True),
    )
    for i, label in enumerate(
        (
            "Scanner eyes · observation",
            "Rounded body · stable identity",
            "RSS tail · transport",
        )
    ):
        draw.text((76, 700 + i * 42), "• " + label, fill="#334155", font=font(20))

    states = ("idle", "scanning", "verified", "healthy", "degraded", "stale", "broken")
    draw.text(
        (560, 52),
        "Operational states",
        fill="#0F172A",
        font=font(28, True),
    )
    for i, name in enumerate(states):
        thumb = fit(
            Image.open(MASCOT / "states" / f"{name}.png").convert("RGBA"),
            (120, 120),
        )
        x = 560 + (i % 4) * 230
        y = 105 + (i // 4) * 190
        board.alpha_composite(thumb, (x, y))
        draw.text((x, y + 126), name.title(), fill="#334155", font=font(17, True))

    draw.text(
        (560, 485),
        "Profile variants",
        fill="#0F172A",
        font=font(28, True),
    )
    profiles = ("developer", "ai-engineer", "founder", "researcher")
    for i, name in enumerate(profiles):
        thumb = fit(
            Image.open(MASCOT / "profiles" / f"{name}.png").convert("RGBA"),
            (150, 150),
        )
        x = 560 + i * 230
        y = 535
        board.alpha_composite(thumb, (x, y))
        draw.text(
            (x, y + 154),
            name.replace("-", " ").title(),
            fill="#334155",
            font=font(16, True),
        )

    tokens = [
        ("#2563EB", "Brand blue"),
        ("#38BDF8", "Signal"),
        ("#10B981", "Healthy"),
        ("#F59E0B", "Degraded"),
        ("#EF4444", "Broken"),
        ("#8B5CF6", "AI accent"),
    ]
    draw.text((560, 760), "Color tokens", fill="#0F172A", font=font(28, True))
    for i, (color, label) in enumerate(tokens):
        x = 560 + i * 145
        draw.ellipse((x, 820, x + 52, 872), fill=color)
        draw.text((x, 885), label, fill="#475569", font=font(13))
        draw.text((x, 907), color, fill="#64748B", font=font(12))

    out = MASCOT / "previews" / "geo-gecko-brand-board.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    board.save(out, optimize=True)


def main() -> None:
    save_png(
        raster(MASCOT / "core.svg", width=1024, square=True),
        MASCOT / "core.png",
    )
    save_png(
        raster(MASCOT / "head.svg", width=1024, square=True),
        MASCOT / "head.png",
    )

    for folder in ("states", "profiles", "stickers"):
        for path in sorted((MASCOT / folder).glob("*.svg")):
            save_png(
                raster(path, width=1024, square=True),
                path.with_suffix(".png"),
            )

    icon_svg = MASCOT / "icons" / "icon.svg"
    for size in (16, 32, 64, 128, 256, 512):
        save_png(
            raster(icon_svg, width=size, square=True),
            MASCOT / "icons" / f"icon-{size}.png",
        )
    icon = Image.open(MASCOT / "icons" / "icon-256.png").convert("RGBA")
    icon.save(
        MASCOT / "icons" / "favicon.ico",
        format="ICO",
        sizes=[
            (16, 16),
            (32, 32),
            (48, 48),
            (64, 64),
            (128, 128),
            (256, 256),
        ],
    )

    save_png(
        raster(MASCOT / "spec" / "palette.svg", width=1200),
        MASCOT / "spec" / "palette.png",
    )
    save_png(
        raster(MASCOT / "spec" / "construction.svg", width=1200, square=True),
        MASCOT / "spec" / "construction.png",
    )
    save_png(
        raster(MASCOT / "social" / "github-avatar.svg", width=1024, square=True),
        MASCOT / "social" / "github-avatar.png",
    )
    save_png(
        raster(MASCOT / "social" / "social-card.svg", width=1200, height=630),
        MASCOT / "social" / "social-card.png",
    )

    contact_sheet()
    brand_board()


if __name__ == "__main__":
    main()
