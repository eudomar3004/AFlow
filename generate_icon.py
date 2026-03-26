"""
generate_icon.py — Generates logo.png, logo_small.png, and AFlow.icns
from logo_full.png (ailoom brand asset).

Steps:
  1. Crop the circular golden badge (isotope) from the left of logo_full.png
  2. Remove the black background to get a transparent badge
  3. Composite centered on a 1024x1024 black square with macOS rounded corners
  4. Draw minimalist sound-wave arcs at the bottom in matte gold
  5. Export logo.png (1024), logo_small.png (256), AFlow.icns
"""

import os
import sys
import shutil
import struct
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

# ── Constants ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
SRC      = BASE_DIR / "logo_full.png"
OUT_LOGO       = BASE_DIR / "logo.png"
OUT_LOGO_SMALL = BASE_DIR / "logo_small.png"
OUT_ICNS       = BASE_DIR / "AFlow.icns"

CANVAS_SIZE  = 1024
CORNER_RATIO = 0.2225          # macOS icon corner radius ≈ 22.25 % of width
BG_COLOR     = (0, 0, 0, 255)  # pure black

# Matte gold palette
GOLD_BASE    = (195, 155,  70)
GOLD_DARK    = (160, 120,  45)
GOLD_LIGHT   = (230, 195, 110)

# ── Helpers ────────────────────────────────────────────────────────────────────

def make_rounded_mask(size: int, radius: int) -> Image.Image:
    """Return an L-mode mask with anti-aliased rounded corners."""
    scale = 4
    big = size * scale
    r   = radius * scale
    mask = Image.new("L", (big, big), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, big - 1, big - 1], radius=r, fill=255)
    return mask.resize((size, size), Image.LANCZOS)


def extract_badge(src: Image.Image) -> Image.Image:
    """
    Isolate the golden circular badge from the left portion of logo_full.png.
    Strategy: any pixel where the gold channel (R) is significantly higher than
    blue is kept; very dark pixels become transparent.
    """
    w, h = src.size
    # The badge occupies roughly the left 38 % of the image
    badge_w = int(w * 0.38)
    crop = src.crop((0, 0, badge_w, h)).convert("RGBA")

    pixels = crop.load()
    for y in range(h):
        for x in range(badge_w):
            r, g, b, a = pixels[x, y]
            luminance = 0.299 * r + 0.587 * g + 0.114 * b
            # Keep only pixels that are visibly gold / bright
            if luminance < 40:           # very dark → transparent
                pixels[x, y] = (0, 0, 0, 0)
            elif r < g + 10 and r < 80:  # bluish/greyish dark → transparent
                pixels[x, y] = (0, 0, 0, 0)

    return crop


def draw_sound_waves(draw: ImageDraw.Draw, cx: int, cy_base: int,
                     canvas: int, n_arcs: int = 3):
    """
    Draw n_arcs concentric half-arcs below cy_base, centered on cx.
    Arcs grow outward; inner arcs are brighter (more opaque).
    """
    # Arc parameters
    gap       = int(canvas * 0.042)   # spacing between arcs
    thickness = max(5, int(canvas * 0.009))
    start_r   = int(canvas * 0.060)   # innermost arc radius

    for i in range(n_arcs):
        r = start_r + i * gap
        alpha = 230 - i * 50          # fade outward
        color = (*GOLD_BASE, alpha)

        # Bounding box for the arc (bottom-half only: 180°→360°)
        bbox = [cx - r, cy_base - r, cx + r, cy_base + r]
        for t in range(thickness):
            off = t - thickness // 2
            b2  = [bbox[0] - off, bbox[1] - off,
                   bbox[2] + off, bbox[3] + off]
            draw.arc(b2, start=180, end=360, fill=color, width=1)


# ── Main ───────────────────────────────────────────────────────────────────────

def build_icon(size: int) -> Image.Image:
    radius = int(size * CORNER_RATIO)

    # ── 1. Background ──────────────────────────────────────────────────────
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    bg     = Image.new("RGBA", (size, size), BG_COLOR)
    mask   = make_rounded_mask(size, radius)
    canvas.paste(bg, mask=mask)

    # ── 2. Badge ───────────────────────────────────────────────────────────
    src   = Image.open(SRC).convert("RGBA")
    badge = extract_badge(src)

    # Trim transparent edges
    bbox  = badge.getbbox()
    if bbox:
        badge = badge.crop(bbox)

    # Scale badge to ~54 % of canvas, preserving aspect
    max_dim  = int(size * 0.54)
    badge_w, badge_h = badge.size
    scale    = min(max_dim / badge_w, max_dim / badge_h)
    new_w    = int(badge_w * scale)
    new_h    = int(badge_h * scale)
    badge    = badge.resize((new_w, new_h), Image.LANCZOS)

    # Badge occupies upper ~60 % of canvas; waves live in lower 28 %
    badge_zone = int(size * 0.62)              # top zone for the badge
    by = max(int(size * 0.05), (badge_zone - new_h) // 2)
    bx = (size - new_w) // 2
    canvas.alpha_composite(badge, dest=(bx, by))

    # ── 3. Sound waves ─────────────────────────────────────────────────────
    overlay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw    = ImageDraw.Draw(overlay)

    cx      = size // 2
    wave_y  = int(size * 0.80)        # fixed at 80 % → always below badge
    draw_sound_waves(draw, cx, wave_y, size, n_arcs=3)
    canvas.alpha_composite(overlay)

    # ── 4. Apply rounded mask ─────────────────────────────────────────────
    r_mask = make_rounded_mask(size, radius)
    canvas.putalpha(r_mask)

    return canvas


def save_icns(src_png: Path, out_icns: Path):
    """Build .icns using iconutil (macOS native)."""
    iconset = out_icns.with_suffix(".iconset")
    iconset.mkdir(exist_ok=True)

    sizes = [
        (16,   "icon_16x16"),
        (32,   "icon_16x16@2x"),
        (32,   "icon_32x32"),
        (64,   "icon_32x32@2x"),
        (128,  "icon_128x128"),
        (256,  "icon_128x128@2x"),
        (256,  "icon_256x256"),
        (512,  "icon_256x256@2x"),
        (512,  "icon_512x512"),
        (1024, "icon_512x512@2x"),
    ]

    img = Image.open(src_png).convert("RGBA")
    for px, name in sizes:
        resized = img.resize((px, px), Image.LANCZOS)
        resized.save(iconset / f"{name}.png", "PNG")

    subprocess.run(
        ["iconutil", "-c", "icns", str(iconset), "-o", str(out_icns)],
        check=True
    )
    shutil.rmtree(iconset)
    print(f"  ✓ {out_icns.name}")


def main():
    print("Generating AFlow icons …")

    # 1024 px master
    icon_1024 = build_icon(1024)
    icon_1024.save(OUT_LOGO, "PNG")
    print(f"  ✓ {OUT_LOGO.name}  (1024 × 1024)")

    # 256 px small
    icon_256 = build_icon(256)
    icon_256.save(OUT_LOGO_SMALL, "PNG")
    print(f"  ✓ {OUT_LOGO_SMALL.name}  (256 × 256)")

    # ICNS
    save_icns(OUT_LOGO, OUT_ICNS)

    print("\nDone. All icon files written to:", BASE_DIR)


if __name__ == "__main__":
    main()
