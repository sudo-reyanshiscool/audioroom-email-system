#!/usr/bin/env python3
"""Process partner logos in source/ into flat-mono email assets in email/.

Pipeline per logo: load -> RGBA -> white-key (only if no real alpha) ->
recolour to #3A3A3A -> trim -> scale to target height -> save optimized.

audioroom.png is the primary mark: trimmed and scaled only, colour
left pure black.
"""

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "source"
OUT = ROOT / "email"
VERSION = "v1"

MONO = (0x3A, 0x3A, 0x3A)

# Target heights in 2x pixels; declared HTML size is half of these.
TARGETS = {
    "gryphon":     52,   # -> 26px displayed
    "piega":       44,   # -> 22px displayed
    "starke":      54,   # -> 27px displayed
    "transparent": 48,   # -> 24px displayed
}

# gryphon.png ships as a lockup with the red crest; the wordmark is the
# grey text. Saturated pixels are the crest and get masked out.
STRIP_SATURATED = {"gryphon"}


def has_meaningful_alpha(img: Image.Image) -> bool:
    lo, hi = img.getchannel("A").getextrema()
    return lo < 250


def process(name: str, target_h: int) -> None:
    matches = sorted(SOURCE.glob(f"{name}.*"))
    if not matches:
        raise SystemExit(f"missing source file: source/{name}.*")
    img = Image.open(matches[0]).convert("RGBA")
    px = img.load()
    w, h = img.size

    if not has_meaningful_alpha(img):
        # Key out the white background: alpha = 255 - luminance.
        for y in range(h):
            for x in range(w):
                r, g, b, _ = px[x, y]
                lum = int(0.299 * r + 0.587 * g + 0.114 * b)
                px[x, y] = (r, g, b, max(0, min(255, 255 - lum)))

    if name in STRIP_SATURATED:
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                if a and (max(r, g, b) - min(r, g, b)) > 15:
                    px[x, y] = (r, g, b, 0)

    # Flat recolour; alpha untouched so edges stay smooth.
    for y in range(h):
        for x in range(w):
            _, _, _, a = px[x, y]
            px[x, y] = (*MONO, a)

    if name in STRIP_SATURATED:
        # Trim on solid pixels only, so faint desaturated crest-edge
        # remnants can't stretch the box; text antialiasing inside it stays.
        bbox = img.getchannel("A").point(lambda a: 255 if a >= 64 else 0).getbbox()
    else:
        bbox = img.getchannel("A").getbbox()
    if bbox is None:
        raise SystemExit(f"{name}: image is fully transparent after processing")
    img = img.crop(bbox)

    scale = target_h / img.height
    # Even 2x width so the declared 1x HTML size is a whole pixel.
    target_w = max(2, 2 * round(img.width * scale / 2))
    img = img.resize((target_w, target_h), Image.LANCZOS)

    out = OUT / f"{name}-{VERSION}.png"
    img.save(out, optimize=True)
    print(f"{out.name}: {img.width}x{img.height}  (1x: {img.width / 2:g}x{img.height / 2:g})")


def main() -> None:
    OUT.mkdir(exist_ok=True)

    for name, target_h in TARGETS.items():
        process(name, target_h)

    # Primary mark: stays pure black, no recolour — only trim the padded
    # canvas and scale to 2x of the 172x29-ish display size (height 58 at 1x 29).
    src = SOURCE / "audioroom.png"
    if not src.exists():
        raise SystemExit("missing source file: source/audioroom.png")
    img = Image.open(src).convert("RGBA")
    bbox = img.getchannel("A").getbbox()
    if bbox is None:
        raise SystemExit("audioroom: image is fully transparent")
    trimmed = img.crop(bbox)

    def scale_to(height: int) -> Image.Image:
        width = max(2, 2 * round(trimmed.width * height / trimmed.height / 2))
        return trimmed.resize((width, height), Image.LANCZOS)

    img = scale_to(58)
    dst = OUT / f"audioroom-{VERSION}.png"
    img.save(dst, optimize=True)
    print(f"{dst.name}: {img.width}x{img.height}  (1x: {img.width // 2}x{img.height // 2}, colour untouched)")

    # Landing-page mark: same crop, larger so it stays crisp on the site.
    site = scale_to(128)
    site_dst = ROOT / "logo.png"
    site.save(site_dst, optimize=True)
    print(f"{site_dst.name}: {site.width}x{site.height}  (1x: {site.width // 2}x{site.height // 2})")


if __name__ == "__main__":
    main()
