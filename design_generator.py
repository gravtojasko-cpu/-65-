"""Generate the CUI design assets for the SkinMenu Rust plugin.

The plugin loads these PNGs from `oxide/data/SkinMenu/design/` through
Rust's `FileStorage` (the same path that vanilla CUI uses). Run this
script once to produce the files, copy them to that folder on your
server, and reload the plugin.

Style: grey palette with sharp / square corners (no rounded edges),
thin lighter-grey borders, and an optional accent stripe on
highlighted variants.

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

from PIL import Image, ImageDraw


def hex_to_rgba(value: str, alpha: int = 255) -> tuple[int, int, int, int]:
    value = value.lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    r = int(value[0:2], 16)
    g = int(value[2:4], 16)
    b = int(value[4:6], 16)
    return r, g, b, alpha


def flat_panel(
    size: tuple[int, int],
    fill: tuple[int, int, int, int],
    border: tuple[int, int, int, int] | None = None,
    border_width: int = 2,
) -> Image.Image:
    """Plain rectangle with sharp (90 degree) corners and an optional border."""
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, size[0] - 1, size[1] - 1), fill=fill)
    if border:
        for i in range(border_width):
            draw.rectangle(
                (i, i, size[0] - 1 - i, size[1] - 1 - i),
                outline=border,
            )
    return img


def vertical_gradient_rect(
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


def draw_background(size: tuple[int, int], accent: str) -> Image.Image:
    base = vertical_gradient_rect(size, (44, 44, 48, 250), (28, 28, 32, 250))

    # Outer border (slightly lighter grey).
    draw = ImageDraw.Draw(base)
    for i in range(2):
        draw.rectangle(
            (i, i, size[0] - 1 - i, size[1] - 1 - i),
            outline=(90, 92, 98, 255),
        )

    # Accent strip across the top edge for a subtle highlight.
    strip = Image.new("RGBA", (size[0] - 8, 3), hex_to_rgba(accent, 200))
    base.paste(strip, (4, 6), strip)

    return base


def draw_slot(size: tuple[int, int], active: bool, accent: str) -> Image.Image:
    if active:
        fill = (60, 62, 70, 240)
        border = hex_to_rgba(accent, 240)
        bw = 3
    else:
        fill = (52, 54, 60, 235)
        border = (95, 97, 104, 255)
        bw = 2
    return flat_panel(size, fill, border=border, border_width=bw)


def draw_button(size: tuple[int, int], accent: str, highlighted: bool) -> Image.Image:
    if highlighted:
        top = (78, 80, 88, 240)
        bot = (52, 54, 60, 240)
        border = hex_to_rgba(accent, 230)
        bw = 2
    else:
        top = (70, 72, 78, 240)
        bot = (46, 48, 54, 240)
        border = (110, 112, 118, 255)
        bw = 2

    grad = vertical_gradient_rect(size, top, bot)
    draw = ImageDraw.Draw(grad)
    for i in range(bw):
        draw.rectangle(
            (i, i, size[0] - 1 - i, size[1] - 1 - i),
            outline=border,
        )
    return grad


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
