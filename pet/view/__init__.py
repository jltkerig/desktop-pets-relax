"""The app's windows and tray, split by job (see each file's docstring):

    frames        sprite frames and timing/drag settings
    discord_pics  lifting the words of a Discord message off its background
    windows       the see-through monitor windows, and the sun/moon window behind everything
    stage         runs the world: mouse, taskbar icons, Discord, desktop folders, the main loop
    toybox        the tray menu and the Toy Box window
"""
from .frames import (
    DRAGGED_ALONG, DRAG_START, FRAME_MS, Frames, PLACED_ITEMS, TASKBAR_REFRESH_MS, TASKBAR_SCRIPT)
from .discord_pics import AVATAR_COLUMN, background_colour, text_only
from .windows import Desktop, SkyWindow
from .stage import Stage
from .toybox import ToyBox, ToyBoxWindow

__all__ = [
    "DRAGGED_ALONG", "DRAG_START", "FRAME_MS", "Frames", "PLACED_ITEMS", "TASKBAR_REFRESH_MS", "TASKBAR_SCRIPT",
    "AVATAR_COLUMN", "background_colour", "text_only", "Desktop", "SkyWindow", "Stage", "ToyBox", "ToyBoxWindow",
]
