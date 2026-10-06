"""Shared by the windows: sprite frames cut from the strips (scaled, facing either way), and a few settings
for timing and dragging."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QTransform
from pathlib import Path

from pet import sprites


FRAME_MS = 33
TASKBAR_SCRIPT = Path(__file__).resolve().parent / "taskbar_buttons.ps1"
TASKBAR_REFRESH_MS = 3 * 60 * 1000
DRAG_START = 6  # pixels the mouse must move before a press becomes a drag
PLACED_ITEMS = ("tree", "birch", "prop", "corn", "crop", "den", "climb", "yard")  # dragged along, and the spot remembered
DRAGGED_ALONG = PLACED_ITEMS + ("pumpkin", "melon")                     # slid along the ground when dragged


class Frames:
    """Loads sprite strips once and cuts them into scaled frames, facing right and left."""

    def __init__(self):
        self.cache = {}

    def get(self, name, frame, scale, facing):
        key = (name, scale)
        if key not in self.cache:
            meta = sprites.meta(name)
            strip = QPixmap(str(sprites.SPRITE_DIR / f"{name}.png"))
            w, h = meta["frame_width"], meta["frame_height"]
            right, left = [], []
            for i in range(meta["frames"]):
                img = strip.copy(i * w, 0, w, h).scaled(w * scale, h * scale, Qt.IgnoreAspectRatio, Qt.FastTransformation)
                right.append(img)
                left.append(img.transformed(QTransform().scale(-1, 1)))
            self.cache[key] = (right, left)
        right, left = self.cache[key]
        frames = right if facing > 0 else left
        return frames[min(frame, len(frames) - 1)]
