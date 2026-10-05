"""The screen saver: the foxes and everything you've put out, filling every monitor, over a sky that follows
the time of day (stars at night) and ground that follows the season. Only a mouse click or a key press closes
it; moving the mouse doesn't (and the pointer is hidden).

Started by "Pixel Fox.scr" (see launcher/), which runs pixelfox.py with --scr and the switch Windows gave it:
/s to run, /c for settings, /p for the little preview (not drawn: the preview box just stays empty).
"""
import copy
import math
import random

from PySide6.QtCore import QElapsedTimer, QRect, Qt, QTimer
from PySide6.QtGui import QColor, QLinearGradient, QPainter
from PySide6.QtWidgets import QMessageBox, QWidget

from pet import screens
from pet.view import Frames
from pet.world import World

GROUND_AT = 0.86  # the ground line, as a share of the screen's height (scenery below it)

# sky colours, top to bottom, for each time of day
SKIES = {
    "day": ("#5f9fd8", "#cde5f6"),
    "dawn": ("#4f62a0", "#f3b487"),
    "dusk": ("#33356c", "#ee8a5c"),
    "night": ("#08122b", "#22335a"),
}
# the ground below the line: (top edge, earth below) per season, and for snow
GROUNDS = {
    "spring": ("#7cb342", "#4f7a2a"),
    "summer": ("#4f9a30", "#33661f"),
    "autumn": ("#9a8a40", "#5e4e26"),
    "winter": ("#7c8a5a", "#4c5236"),
    "snow": ("#f2f6fa", "#c8d4e2"),
}
# grass along the ground line: blade colours (dark, mid, light) per season. Fresh in spring, deep in summer,
# golden and russet in autumn, dull and straw-coloured in winter; under snow only a few tips poke through.
GRASS = {
    "spring": ("#4e8a1e", "#78b830", "#a8dc5a"),
    "summer": ("#2e6a1a", "#46902a", "#6cb844"),
    "autumn": ("#8a6a24", "#b8963a", "#c8783a"),
    "winter": ("#6a6a48", "#8c8a5c", "#a8a070"),
    "snow": ("#6a6a48", "#8c8a5c", "#a8a070"),
}


def saver_settings(settings, screen_height):
    """A copy of your settings for the screen saver: everything drawn bigger to fill the screen, and none of
    the desktop mischief (there are no windows to steal from or taskbar icons to dig up). Nothing it does is
    saved."""
    s = copy.deepcopy(settings)
    s["scale"] = max(2, screen_height // 360)
    s["mischief"] = {key: False for key in s.get("mischief", {})}
    return s


class SaverWindow(QWidget):
    """One monitor's part of the screen saver."""

    def __init__(self, saver, screen, slice_):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.saver, self.world = saver, saver.world
        self.setScreen(screen)
        self.setGeometry(QRect(slice_["x"], slice_["y"], slice_["w"], slice_["h"]))
        self.setCursor(Qt.BlankCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.dx = -slice_["offset"]                                   # strip x -> this window's x
        self.ground_y = int(slice_["h"] * GROUND_AT)
        self.dy = self.ground_y - self.world.ground                   # line the world's ground up with ours
        rng = random.Random(slice_["offset"])
        self.stars = [(rng.randrange(slice_["w"]), rng.randrange(int(self.ground_y * 0.8)), rng.uniform(0, 6.3))
                      for _ in range(slice_["w"] * slice_["h"] // 9000)]
        # grass blades along the ground: (x, height, lean, shade, phase), in screen pixels
        s = self.world.scale
        self.blades = [(x, rng.uniform(3, 9) * s, rng.uniform(-1.5, 1.5) * s, rng.randrange(3), rng.uniform(0, 6.3))
                       for x in range(0, slice_["w"], max(2, s)) if rng.random() < 0.7]
        # a few lighter and darker patches in the earth, so it isn't one flat colour
        self.clods = [(rng.randrange(slice_["w"]), rng.randrange(self.ground_y + 3 * s, slice_["h"]),
                       rng.randrange(2, 6) * s, rng.choice((-1, 1))) for _ in range(slice_["w"] // 14)]

    def paintEvent(self, event):
        painter = QPainter(self)
        w, h = self.width(), self.height()
        light = self.world.daylight()
        top, bottom = SKIES.get(light, SKIES["day"])
        sky = QLinearGradient(0, 0, 0, self.ground_y)
        sky.setColorAt(0, QColor(top))
        sky.setColorAt(1, QColor(bottom))
        painter.fillRect(0, 0, w, self.ground_y, sky)
        if light in ("night", "dawn", "dusk"):
            t = self.saver.elapsed
            fade = 1.0 if light == "night" else 0.35
            for x, y, phase in self.stars:
                twinkle = 0.55 + 0.45 * ((t * 1.3 + phase) % 6.3 > 3.15)
                painter.fillRect(x, y, 2, 2, QColor(255, 255, 240, int(220 * fade * twinkle)))
        self.paint_ground(painter, w, h)
        for thing in self.world.drawing_order():
            if thing.kind in ("treasure", "message"):
                continue  # pictures copied off the desktop: never in the screen saver
            left, top_, tw, th = thing.rect()
            x, y = int(round(left + self.dx)), int(round(top_ + self.dy))
            if x > w or y > h or x + tw < 0 or y + th < 0:
                continue  # on another monitor
            painter.setOpacity(max(0.0, min(1.0, thing.alpha)))
            painter.drawPixmap(x, y, self.saver.frames.get(thing.anim.name, thing.anim.frame, self.world.scale,
                                                           thing.facing))
        painter.end()

    def paint_ground(self, painter, w, h):
        """The earth below the ground line and the grass growing along it, coloured for the season."""
        season = self.world.season
        look = "snow" if season == "winter" and self.world.snowy else season
        edge, earth = GROUNDS[look]
        s = self.world.scale
        painter.fillRect(0, self.ground_y, w, h - self.ground_y, QColor(earth))
        for x, y, size, tone in self.clods:
            painter.fillRect(x, y, size, max(1, size // 2), QColor(earth).lighter(112) if tone > 0 else
                             QColor(earth).darker(115))
        painter.fillRect(0, self.ground_y, w, max(4, s * 3), QColor(edge))
        colours = [QColor(c) for c in GRASS[look]]
        sway = self.world.wind * 4 * s
        t = self.saver.elapsed
        for x, height, lean, shade, phase in self.blades:
            if look == "snow":
                if phase > 1.2:
                    continue  # buried: only the odd tip pokes through the snow
                height *= 0.45
            tip = lean + (math.sin(t * 1.5 + phase) * 0.6 * s + sway) * (height / (9 * s))
            steps = max(1, int(height // s))
            for k in range(steps):  # a blade: a column of pixels, leaning more toward the tip
                f = (k + 1) / steps
                painter.fillRect(int(x + tip * f * f), int(self.ground_y - (k + 1) * s), s, s,
                                 colours[min(2, shade + (k * 2 // steps))])

    # only a click or a key press ends the screen saver; moving the mouse does nothing
    def mousePressEvent(self, event):
        self.saver.close()

    def keyPressEvent(self, event):
        self.saver.close()


class Saver:
    """Runs the screen saver across every monitor, all showing one world."""

    def __init__(self, app, settings):
        self.app = app
        screens_ = app.screens()
        areas = [(g.x(), g.y(), g.width(), g.height()) for g in (s.geometry() for s in screens_)]
        slices, width, height = screens.layout(areas)
        main_h = min(s["h"] for s in slices)
        ground = int(main_h * GROUND_AT)
        self.world = World(width, ground + 2, saver_settings(settings, main_h),
                           seams=[s["offset"] for s in slices[1:]])
        self.frames = Frames()
        self.elapsed = 0.0  # before any window shows: they use it to twinkle the stars
        by_corner = {(s.geometry().x(), s.geometry().y()): s for s in screens_}
        self.windows = [SaverWindow(self, by_corner.get((sl["x"], sl["y"]), screens_[0]), sl) for sl in slices]
        for win in self.windows:
            win.showFullScreen()
        self.windows[0].activateWindow()
        self.windows[0].setFocus()
        self.clock = QElapsedTimer()
        self.clock.start()
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(33)

    def tick(self):
        dt = self.clock.restart() / 1000
        self.elapsed += dt
        self.world.update(dt, None)
        for win in self.windows:
            win.update()

    def close(self):
        self.timer.stop()
        for win in self.windows:
            win.close()
        self.app.quit()


def mode(args):
    """What Windows asked the screen saver for: "run" (/s), "settings" (/c, or nothing), or "preview" (/p)."""
    switch = (args[0] if args else "/c").lower().lstrip("/-")
    return {"s": "run", "p": "preview"}.get(switch[:1], "settings")


def settings_box():
    QMessageBox.information(
        None, "Pixel Fox screen saver",
        "The screen saver shows your foxes and the things you've put out in the Toy Box, filling the screen.\n\n"
        "Only a mouse click or a key press closes it: moving the mouse doesn't.")
