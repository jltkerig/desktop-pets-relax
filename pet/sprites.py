"""Sprite strips: art/sprites/<name>.png plus <name>.json. This part has no Qt, so tests can use it."""
import json
from functools import lru_cache
from pathlib import Path

SPRITE_DIR = Path(__file__).resolve().parents[1] / "art" / "sprites"


@lru_cache(maxsize=None)
def meta(name):
    """{"frame_width", "frame_height", "frames", "ms", "loop", "anchor"} for a sprite."""
    data = json.loads((SPRITE_DIR / f"{name}.json").read_text(encoding="utf-8"))
    data["ms"] = max(16, int(data.get("ms", 100)))
    data["loop"] = bool(data.get("loop", True))
    data["anchor"] = tuple(data.get("anchor", (data["frame_width"] // 2, data["frame_height"] - 1)))
    return data


def exists(name):
    return (SPRITE_DIR / f"{name}.json").is_file() and (SPRITE_DIR / f"{name}.png").is_file()


def duration(name):
    """Seconds one pass of the animation takes."""
    m = meta(name)
    return m["frames"] * m["ms"] / 1000


class Anim:
    """Plays one sprite: which frame is showing, and whether a non-looping one has finished."""

    def __init__(self, name):
        self.name = name
        self.time = 0.0
        self.done = False

    def update(self, dt):
        self.time += dt
        m = meta(self.name)
        if not m["loop"] and self.time >= duration(self.name):
            self.done = True

    @property
    def frame(self):
        m = meta(self.name)
        index = int(self.time * 1000 // m["ms"])
        return index % m["frames"] if m["loop"] else min(index, m["frames"] - 1)

    def play(self, name):
        """Switch to another sprite (a no-op if it's already playing and still running)."""
        if name != self.name or self.done:
            self.name, self.time, self.done = name, 0.0, False
