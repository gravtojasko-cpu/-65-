"""Generate the CUI design assets for the SkinMenu Rust plugin.

The plugin loads these PNGs from `oxide/data/SkinMenu/design/` through
ImageLibrary. Run this script once to produce the files, copy them to
that folder on your server (or symlink it during development), and
reload the plugin.

Usage:
    python design_generator.py --out ./design

Optional flags:
    --width / --height : output canvas size in pixels
    --accent            : accent colour hex (default #2E8FE0)

Requires: Pillow (`pip install pillow`).
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


def hex_to_rgba(value: str, alpha: int = 255) -> tuple[int, int, int, int]:
    value = value.lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    r = int(value[0:2], 16)
    g = int(value[2:4], 16)
    b = int(value[4:6], 16)
    return r, g, b, alpha


def rounded_panel(
    size: tuple[int, int],
    fill: tuple[int, int, int, int],
    radius: int = 24,
    border: tuple[int, int, int, int] | None = None,
    border_width: int = 2,
) -> Image.Image:
    """Draw a rounded rectangle on a transparent canvas."""
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=radius, fill=fill)
    if border:
        draw.rounded_rectangle(
            (0, 0, size[0] - 1, size[1] - 1),
            radius=radius,
            outline=border,
            width=border_width,
        )
    return img


def vertical_gradient(
    size: tuple[int, int],
    top: tuple[int, int, int, int],
    bottom: tuple[int, int, int, int],
) -> Image.Image:
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    pixels = img.load()
    h = size[1]
    for y in range(h):
        t = y / max(1, h - 1)
        r = int(top[0] * (1 - t) + bottom[0] * t)
        g = int(top[1] * (1 - t) + bottom[1] * t)
        b = int(top[2] * (1 - t) + bottom[2] * t)
        a = int(top[3] * (1 - t) + bottom[3] * t)
        for x in range(size[0]):
            pixels[x, y] = (r, g, b, a)
    return img


def apply_alpha_mask(image: Image.Image, mask: Image.Image) -> Image.Image:
    """Clip `image` to the alpha channel of `mask`."""
    if image.size != mask.size:
        image = image.resize(mask.size)
    base = Image.new("RGBA", mask.size, (0, 0, 0, 0))
    base.paste(image, mask=mask.split()[-1])
    return base


def draw_background(size: tuple[int, int], accent: str) -> Image.Image:
    bg = vertical_gradient(size, (18, 19, 24, 245), (10, 11, 14, 245))
    mask = rounded_panel(size, (255, 255, 255, 255), radius=28)
    panel = apply_alpha_mask(bg, mask)

    # Accent strip across the top.
    strip = Image.new("RGBA", (size[0] - 80, 4), hex_to_rgba(accent, 220))
    panel.paste(strip, (40, 36), strip)

    # Soft inner glow.
    glow = Image.new("RGBA", size, (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(glow)
    g_draw.rounded_rectangle((6, 6, size[0] - 7, size[1] - 7), radius=24,
                             outline=hex_to_rgba(accent, 60), width=2)
    glow = glow.filter(ImageFilter.GaussianBlur(4))
    panel = Image.alpha_composite(panel, glow)

    return panel


def draw_slot(size: tuple[int, int], active: bool, accent: str) -> Image.Image:
    if active:
        fill = hex_to_rgba(accent, 80)
        border = hex_to_rgba(accent, 230)
        bw = 3
    else:
        fill = (30, 31, 36, 230)
        border = (60, 62, 70, 255)
        bw = 2

    img = rounded_panel(size, fill, radius=12, border=border, border_width=bw)
    # subtle inner shadow
    inner = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(inner)
    d.rounded_rectangle((2, 2, size[0] - 3, size[1] - 3), radius=10,
                        outline=(0, 0, 0, 90), width=1)
    img = Image.alpha_composite(img, inner)
    return img


def draw_button(size: tuple[int, int], accent: str, highlighted: bool) -> Image.Image:
    if highlighted:
        top = hex_to_rgba(accent, 240)
        bot = hex_to_rgba(accent, 200)
        border = (255, 255, 255, 70)
    else:
        top = (45, 47, 55, 235)
        bot = (28, 30, 36, 235)
        border = (90, 92, 100, 200)

    grad = vertical_gradient(size, top, bot)
    mask = rounded_panel(size, (255, 255, 255, 255), radius=10)
    btn = apply_alpha_mask(grad, mask)

    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=10,
                        outline=border, width=2)
    btn = Image.alpha_composite(btn, overlay)
    return btn


ASSETS: list[tuple[str, tuple[int, int]]] = [
    ("bg.png", (1280, 800)),
    ("slot.png", (192, 192)),
    ("slot_active.png", (192, 192)),
    ("button.png", (320, 96)),
    ("button_hl.png", (320, 96)),
]


def generate(out_dir: Path, accent: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    for name, size in ASSETS:
        if name == "bg.png":
            img = draw_background(size, accent)
        elif name == "slot.png":
            img = draw_slot(size, active=False, accent=accent)
        elif name == "slot_active.png":
            img = draw_slot(size, active=True, accent=accent)
        elif name == "button.png":
            img = draw_button(size, accent, highlighted=False)
        elif name == "button_hl.png":
            img = draw_button(size, accent, highlighted=True)
        else:
            continue

        path = out_dir / name
        img.save(path, "PNG")
        print(f"wrote {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate SkinMenu design assets.")
    parser.add_argument(
        "--out",
        default=os.path.join("oxide", "data", "SkinMenu", "design"),
        help="Output directory (default: oxide/data/SkinMenu/design)",
    )
    parser.add_argument("--accent", default="#2E8FE0", help="Accent colour hex")
    args = parser.parse_args()

    generate(Path(args.out), args.accent)


if __name__ == "__main__":
    main()
