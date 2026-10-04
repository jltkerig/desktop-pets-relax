"""Draws every sprite and writes art/sprites/<name>.png (a horizontal strip of frames) and <name>.json.

    python art/make_art.py            # everything
    python art/make_art.py --preview  # also art/preview.png, every animation enlarged, for checking by eye

To use your own art instead, replace a PNG and its JSON (same name); the app reads only these files.
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fox_art  # noqa: E402
import world_art  # noqa: E402

OUT = Path(__file__).resolve().parent / "sprites"
FOX_PALETTES = ("orange", "grey")


def save_strip(name, frames, ms, loop, anchor=None, extra=None):
    """frames: PIL images of one size. anchor: the point (in the frame) that sits on the ground / the item's
    position; defaults to bottom centre. extra: anything else to write into the JSON."""
    w, h = frames[0].size
    strip = Image.new("RGBA", (w * len(frames), h), (0, 0, 0, 0))
    for i, frame in enumerate(frames):
        strip.paste(frame, (i * w, 0))
    strip.save(OUT / f"{name}.png")
    meta = {"frame_width": w, "frame_height": h, "frames": len(frames), "ms": ms, "loop": loop,
            "anchor": list(anchor or (w // 2, h - 1))}
    for key, value in (extra or {}).items():
        meta[key] = [[round(v, 1) for v in point] for point in value] if key == "perches" else value
    (OUT / f"{name}.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return strip


def build():
    OUT.mkdir(exist_ok=True)
    made = {}
    for palette in FOX_PALETTES:
        for anim, (frames, ms, loop) in fox_art.ANIMATIONS.items():
            images = [fox_art.fox(**dict(f, palette=palette)) for f in frames]
            made[f"fox_{palette}_{anim}"] = save_strip(f"fox_{palette}_{anim}", images, ms, loop,
                                                       anchor=(32 + fox_art.ROOM, fox_art.GROUND))
    for name, (frames, ms, loop, anchor, *extra) in world_art.SPRITES.items():
        made[name] = save_strip(name, frames, ms, loop, anchor, *extra)
    return made


def preview(made, scale=3):
    rows = list(made.items())
    width = max(img.width for _, img in rows) * scale + 220
    height = sum(img.height * scale + 8 for _, img in rows)
    sheet = Image.new("RGBA", (width, height), (232, 238, 230, 255))
    draw = ImageDraw.Draw(sheet)
    y = 0
    for name, img in rows:
        draw.text((6, y + 4), name, fill=(40, 40, 40, 255))
        big = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
        sheet.alpha_composite(big, (210, y))
        y += big.height + 8
    sheet.save(Path(__file__).resolve().parent / "preview.png")


if __name__ == "__main__":
    made = build()
    if "--preview" in sys.argv:
        preview(made)
    print(f"Wrote {len(made)} sprites to {OUT}")
