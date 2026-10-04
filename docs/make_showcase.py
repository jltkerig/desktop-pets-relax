"""Builds docs/showcase.png for the README: an autumn scene made from the app's own sprites.

    python docs/make_showcase.py
"""
import json
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SPRITES = ROOT / "art" / "sprites"
SCALE = 2
W, H = 1800, 560
GROUND = H - 70


def frame(name, index=0, flip=False):
    meta = json.loads((SPRITES / f"{name}.json").read_text(encoding="utf-8"))
    strip = Image.open(SPRITES / f"{name}.png").convert("RGBA")
    fw, fh = meta["frame_width"], meta["frame_height"]
    img = strip.crop((index * fw, 0, (index + 1) * fw, fh)).resize((fw * SCALE, fh * SCALE), Image.NEAREST)
    ax, ay = meta["anchor"]
    if flip:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
        ax = fw - ax
    return img, ax * SCALE, ay * SCALE


def put(scene, name, x, y=GROUND, index=0, flip=False):
    img, ax, ay = frame(name, index, flip)
    scene.alpha_composite(img, (int(x - ax), int(y - ay)))


def main():
    scene = Image.new("RGBA", (W, H))
    draw = ImageDraw.Draw(scene)
    for y in range(H):  # an autumn sky, warmer toward the ground
        t = y / H
        draw.line([(0, y), (W, y)], fill=(int(150 + 90 * t), int(190 + 30 * t), int(230 - 40 * t), 255))
    draw.rectangle([0, GROUND, W, H], fill=(46, 48, 56, 255))          # a taskbar to stand on
    draw.rectangle([0, GROUND, W, GROUND + 2], fill=(70, 72, 82, 255))

    for i, (x, y) in enumerate(((860, 90), (886, 104), (886, 76), (912, 118), (912, 62), (938, 132), (938, 48))):  # geese flying south
        put(scene, "goose_far", x, y, index=i % 4, flip=True)
    put(scene, "corn_3", 120)
    put(scene, "hoe", 245)
    put(scene, "pumpkin_4_l_round", 300, index=1)
    put(scene, "pumpkin_4_m_tall_jack", 380, index=0)
    put(scene, "pumpkin_4_s_squat", 455)
    put(scene, "scarecrow", 540, index=2)
    put(scene, "haystack_steps", 700)
    put(scene, "fox_grey_idle", 735, GROUND - 47 * SCALE, index=1, flip=True)   # sitting on top of the hay
    put(scene, "den_orange", 930)
    put(scene, "woolly", 1060, index=2)
    put(scene, "oak", 1300, index=1)
    put(scene, "jay_perch", 1255, GROUND - 188 * SCALE)
    put(scene, "squirrel_sit", 1215, index=1, flip=True)
    put(scene, "acorn", 1400)
    put(scene, "fox_orange_pounce", 1440, GROUND - 26 * SCALE, index=2, flip=True)
    for i, (x, y, colour) in enumerate(((1180, 200, "red"), (1360, 260, "yellow"), (1440, 330, "orange"),
                                        (1230, 370, "brown"), (1500, 230, "red"))):
        put(scene, f"leaf_{colour}", x, y, index=i % 6)
    put(scene, "barrels", 1650)
    out = Path(__file__).resolve().parent / "showcase.png"
    scene.convert("RGB").save(out, optimize=True)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
