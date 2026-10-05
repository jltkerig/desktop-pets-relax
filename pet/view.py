"""The see-through window the pets live in, and the tray menu (the toy box).

The window covers the desktop above the taskbar. It is transparent, so clicks on empty pixels go straight
to the desktop; only the foxes, the tree and the other things catch the mouse.
"""
import json
from pathlib import Path

from PySide6.QtCore import QElapsedTimer, QPoint, QProcess, QRect, Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup, QColor, QCursor, QIcon, QImage, QPainter, QPixmap, QTransform
from PySide6.QtWidgets import (QApplication, QCheckBox, QGroupBox, QLabel, QMenu, QPushButton, QSystemTrayIcon,
                               QTabWidget, QVBoxLayout, QWidget)

from pet import __version__, desktop_icons, discord, save, screens, seasons, sky, sprites, weather

FRAME_MS = 33
TASKBAR_SCRIPT = Path(__file__).resolve().parent / "taskbar_buttons.ps1"
TASKBAR_REFRESH_MS = 3 * 60 * 1000
DRAG_START = 6  # pixels the mouse must move before a press becomes a drag
PLACED_ITEMS = ("tree", "birch", "prop", "corn", "crop", "den", "climb")  # dragged along, and the spot remembered
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


AVATAR_COLUMN = 44  # Qt pixels at the left of the chat column where avatars are (never taken)


def text_only(image, background, skip_left=0):
    """Just the text out of a picture of a Discord message: (picture with the background see-through, the part
    of the original it came from as a QRect), or None if there's no text. background: a QColor."""
    w, h = image.width(), image.height()
    br, bg_, bb = background.red(), background.green(), background.blue()

    def diff(c):
        return max(abs(c.red() - br), abs(c.green() - bg_), abs(c.blue() - bb))

    xs, ys = [], []
    for y in range(h):
        for x in range(max(0, skip_left), w):
            if diff(image.pixelColor(x, y)) > 48:
                xs.append(x)
                ys.append(y)
    if len(xs) < 12:
        return None
    left, right = max(skip_left, min(xs) - 2), min(w - 1, max(xs) + 2)
    top, bottom = max(0, min(ys) - 2), min(h - 1, max(ys) + 2)
    out = QImage(right - left + 1, bottom - top + 1, QImage.Format_ARGB32)
    out.fill(Qt.transparent)
    for y in range(top, bottom + 1):
        for x in range(left, right + 1):
            c = image.pixelColor(x, y)
            d = diff(c)
            if d >= 14:  # text (its soft edges partly see-through)
                out.setPixelColor(x - left, y - top, QColor(c.red(), c.green(), c.blue(), min(255, (d - 14) * 4)))
    # a thin dark outline round the letters, so they read on grass, sky or snow
    ow, oh = out.width(), out.height()
    solid = {(x, y) for y in range(oh) for x in range(ow) if out.pixelColor(x, y).alpha() > 120}
    edge = QColor(max(0, br - 20), max(0, bg_ - 20), max(0, bb - 20), 200)
    for x, y in solid:
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < ow and 0 <= ny < oh and (nx, ny) not in solid and out.pixelColor(nx, ny).alpha() < 120:
                out.setPixelColor(nx, ny, edge)
    return out, QRect(left, top, right - left + 1, bottom - top + 1)


def background_colour(image):
    """The plain colour all round the edge of a picture (Discord's background behind a message), or None if
    the edges aren't mostly one colour (or the picture is empty)."""
    if image.isNull() or image.width() < 8 or image.height() < 4:
        return None
    w, h = image.width(), image.height()
    edge = [(x, y) for x in range(0, w, 3) for y in (0, 1, h - 2, h - 1)] + \
           [(x, y) for y in range(0, h, 2) for x in (0, 1, 2, w - 3, w - 2, w - 1)]
    counts = {}
    for x, y in edge:
        rgb = image.pixelColor(x, y).rgb() & 0xFFFFFF
        counts[rgb] = counts.get(rgb, 0) + 1
    rgb, n = max(counts.items(), key=lambda kv: kv[1])
    if n < len(edge) * 0.6:
        return None
    if rgb == 0 and n == len(edge) and all(image.pixelColor(x, y).rgb() & 0xFFFFFF == 0
                                           for x in range(0, w, 4) for y in range(0, h, 4)):
        return None  # all black: the screen couldn't be copied
    return QColor(rgb >> 16 & 255, rgb >> 8 & 255, rgb & 255)


class Stage:
    """Runs the pets across every monitor: one see-through window per monitor, all showing slices of the
    same world. Notices monitors being plugged in, unplugged or rearranged, and rebuilds."""

    def __init__(self, world, settings):
        self.world, self.settings = world, settings
        self.frames = Frames()
        self.desktops = []
        self.press = None       # (thing, press point in the strip, thing's start x)
        self.trail = []         # (time, x, y) of the cursor lately, while holding a ball: how hard it's thrown
        self.dragging = None
        self.last_pet = 0.0
        self.elapsed = 0.0
        self.clock = QElapsedTimer()
        self.clock.start()
        self._watched = set()
        self.build()
        app = QApplication.instance()
        for signal in (app.screenAdded, app.screenRemoved, app.primaryScreenChanged):
            signal.connect(lambda *_: QTimer.singleShot(500, self.build))
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(FRAME_MS)
        # where the taskbar icons are (for digging up "treasure"); checked now and every few minutes
        self.taskbar_strip = None
        self.finder = QProcess()
        self.finder.finished.connect(self._taskbar_found)
        self.find_taskbar()
        self.taskbar_timer = QTimer()
        self.taskbar_timer.timeout.connect(self.find_taskbar)
        self.taskbar_timer.start(TASKBAR_REFRESH_MS)
        # Discord mischief: where a message could be stolen from, and the covers over stolen messages
        self.discord = None          # (hwnd, bounds, band QRect in screen pixels)
        self.covers = {}             # message key -> (QRect in screen pixels, QColor, hwnd, bounds)
        self.discord_timer = QTimer()
        self.discord_timer.timeout.connect(self.look_for_discord)
        self.discord_timer.start(15000)
        self.guard_timer = QTimer()
        self.guard_timer.timeout.connect(self.guard_covers)
        self.guard_timer.start(500)
        self.active_timer = QTimer()  # every couple of seconds: are you using Discord right now?
        self.active_timer.timeout.connect(self.check_discord_use)
        self.active_timer.start(2000)
        # rain and snow from the local weather, fetched in the background every half hour
        self.weather = weather.Watcher(self.settings).start()
        # the sun or the moon, behind every window, moved along its arc every half minute
        self.sky = SkyWindow(self)
        self.sky.place()
        self.sky_timer = QTimer()
        self.sky_timer.timeout.connect(self.sky.place)
        self.sky_timer.start(30000)
        self.shimmer = QTimer()  # the sun's rays shimmer
        self.shimmer.timeout.connect(lambda: self.sky.update() if self.sky.isVisible() else None)
        self.shimmer.start(900)
        # the folder icons on the desktop, for the foxes to move about (looked for every few seconds)
        self.movers = {}  # folder name -> desktop_icons.Mover, while a fox has it
        self.folder_timer = QTimer()
        self.folder_timer.timeout.connect(self.look_for_folders)
        self.folder_timer.start(5000)

    def check_discord_use(self):
        if not self.world.mischief("discord"):
            self.world.discord_active = False
            return
        found = self.discord[0] if self.discord else None
        if found is None:
            window = discord.find_window()
            found = window[0] if window else None
        active = found is not None and discord.in_use(found)
        if active and not self.world.discord_active and not self.covers:
            self.look_for_discord()  # fresh: where's a message showing right now?
        self.world.discord_active = active and self.world.discord_spot is not None

    # -- Discord mischief ------------------------------------------------------------------------------

    def look_for_discord(self):
        """Is there a visible Discord window with a message showing? Tell the world where."""
        self.discord = None
        self.world.discord_spot = None
        if not self.world.mischief("discord") or self.covers:
            return
        found = discord.find_window()
        if not found:
            return
        hwnd, (left, top, right, bottom) = found
        ratio = QApplication.primaryScreen().devicePixelRatio()
        # the chat column: past the server and channel lists, short of the member list and the typing box.
        # (Discord's layout grows with the display scaling, and these are physical pixels, hence * ratio.)
        x0, x1 = left + 340 * ratio, min(right - 260 * ratio, left + (340 + 520) * ratio)
        if x1 - x0 < 200 * ratio:
            return
        for lift in (150, 210, 270, 330, 390):
            band = QRect(int(x0), int(bottom - (lift + 46) * ratio), int(x1 - x0), int(46 * ratio))
            corners = (band.topLeft(), band.topRight(), band.bottomLeft(), band.bottomRight(), band.center())
            if not all(discord.shows_at(hwnd, p.x(), p.y()) for p in corners):
                continue  # something covers this part of Discord
            logical = QRect(int(band.x() / ratio), int(band.y() / ratio), int(band.width() / ratio), int(band.height() / ratio))
            image = QApplication.primaryScreen().grabWindow(0, logical.x(), logical.y(), logical.width(), logical.height()).toImage()
            if image.isNull():
                continue
            bg = background_colour(image)
            if bg is None:
                continue  # not a plain background here (a picture, an embed...): leave it alone
            busy = sum(1 for y in range(0, image.height(), 3) for x in range(0, image.width(), 3)
                       if abs(image.pixelColor(x, y).lightness() - bg.lightness()) > 40)
            if busy > 25:  # some text here: a message
                self.discord = (hwnd, (left, top, right, bottom), logical)
                bottom_mid = QPoint(logical.center().x(), logical.bottom())
                x, y = self.to_world(bottom_mid)
                if x > -9999:
                    self.world.discord_spot = {"x": x, "y": y}
                return

    def _handle_screen_requests(self):
        while self.world.screen_requests:
            action, key = self.world.screen_requests.pop(0)
            if action == "steal":
                self._steal(key)
            elif action == "restore":
                self.covers.pop(key, None)
                self.update()

    def _steal(self, key):
        if not self.discord:
            self.world.cancel_message(key)
            return
        hwnd, bounds, band = self.discord
        if not discord.still_there(hwnd, bounds):
            self.world.cancel_message(key)
            return
        corners = (band.topLeft(), band.topRight(), band.bottomLeft(), band.bottomRight(), band.center())
        ratio = QApplication.primaryScreen().devicePixelRatio()
        if not all(discord.shows_at(hwnd, p.x() * ratio, p.y() * ratio) for p in corners):
            self.world.cancel_message(key)  # something's in front of it now
            return
        picture = QApplication.primaryScreen().grabWindow(0, band.x(), band.y(), band.width(), band.height())
        image = picture.toImage()
        cover = background_colour(image)  # Discord's background colour, to hide the gap
        if image.isNull() or cover is None:
            self.world.cancel_message(key)  # couldn't see it properly: better not to steal anything
            return
        # just the words: past the avatar column, cropped to the text, Discord's background made see-through
        to_image = image.width() / max(1, band.width())  # logical -> picture pixels
        found = text_only(image, cover, skip_left=int(AVATAR_COLUMN * to_image))
        if found is None:
            self.world.cancel_message(key)  # no text there after all
            return
        words, crop = found
        gap = QRect(band.x() + int(crop.x() / to_image), band.y() + int(crop.y() / to_image),
                    int(crop.width() / to_image) + 1, int(crop.height() / to_image) + 1)
        picture = QPixmap.fromImage(words)
        width = min(gap.width(), 150 * self.world.scale)
        small = picture.scaledToWidth(int(width), Qt.SmoothTransformation)
        self.world.images[key] = small
        home = self.to_world(QPoint(gap.center().x(), gap.bottom()))
        for msg in self.world.of("message"):
            if msg.key == key:
                msg.size = (float(small.width()), float(small.height()))
                if home[0] > -9999:  # it flies back to where the words were
                    msg.home = home
                    if msg.state == "home":
                        msg.x, msg.y = home
        self.covers[key] = (gap, cover, hwnd, bounds)
        self.update()

    def guard_covers(self):
        """If the Discord window moves, closes or gets covered, the gap disappears at once. A cover whose
        message no longer exists (for whatever reason) is taken away too, so a gap can never get stuck."""
        alive = {m.key for m in self.world.of("message")}
        for key in [k for k in self.covers if k not in alive]:
            self.covers.pop(key, None)
            self.update()
        for key, (band, _, hwnd, bounds) in list(self.covers.items()):
            ratio = QApplication.primaryScreen().devicePixelRatio()
            centre = band.center()
            if not discord.still_there(hwnd, bounds) or not discord.shows_at(hwnd, centre.x() * ratio, centre.y() * ratio):
                self.covers.pop(key, None)
                self.world.cancel_message(key)
                self.update()

    # -- the monitors ----------------------------------------------------------------------------------

    def build(self):
        """(Re)make one window per monitor, from whatever monitors there are right now."""
        found = []
        for screen in QApplication.screens():
            a = screen.availableGeometry()
            found.append((a.x(), a.y(), a.width(), a.height(), screen))
        slices, width, height = screens.layout([f[:4] for f in found])
        by_area = {f[:4]: f[4] for f in found}
        for desktop in self.desktops:
            desktop.hide()
            desktop.deleteLater()
        self.world.resize(width, height)
        self.world.set_seams([s["offset"] for s in slices[1:]])
        self.desktops = []
        for s in slices:
            screen = by_area[(s["x"], s["y"], s["w"], s["h"])]
            desktop = Desktop(self, screen, s)
            desktop.show()
            self.desktops.append(desktop)
        if getattr(self, "sky", None) is not None:
            QTimer.singleShot(0, self.sky.place)
        for screen in QApplication.screens():  # a taskbar moved or resized, a resolution changed
            if screen not in self._watched:
                self._watched.add(screen)
                screen.availableGeometryChanged.connect(lambda *_: QTimer.singleShot(500, self.build))

    def to_world(self, global_point):
        """A point on any monitor -> (x, y) along the strip; far away if it's on no monitor."""
        for d in self.desktops:
            if d.geometry().contains(global_point):
                local = d.mapFromGlobal(global_point)
                return d.to_world(local.x(), local.y())
        return (-10000.0, -10000.0)

    def update(self):
        for d in self.desktops:
            d.update()

    # -- the taskbar icons (on the main monitor) ---------------------------------------------------------

    def main_desktop(self):
        primary = QApplication.primaryScreen()
        return next((d for d in self.desktops if d.screen_ is primary), self.desktops[0] if self.desktops else None)

    def find_taskbar(self):
        if self.finder.state() == QProcess.NotRunning:
            self.finder.start("powershell", ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(TASKBAR_SCRIPT)])

    def _taskbar_found(self):
        main = self.main_desktop()
        try:
            strip = json.loads(bytes(self.finder.readAllStandardOutput()).decode("utf-8", "replace") or "{}")
            ratio = main.screen_.devicePixelRatio()
            strip = {k: strip[k] / ratio for k in ("x", "y", "w", "h")}
        except (ValueError, KeyError, TypeError, AttributeError):
            return
        if strip["w"] < 20 or strip["h"] < 10:
            return
        self.taskbar_strip = strip
        self.world.taskbar_spots = self._icon_spots(main, strip)

    def _icon_spots(self, main, strip):
        """Where each taskbar icon is, along the strip.

        Columns where the middle of the bar differs from the plain bar colour are part of an icon; runs of
        such columns about an icon wide are icons.
        """
        image = main.screen_.grabWindow(0, int(strip["x"]), int(strip["y"]), int(strip["w"]), int(strip["h"])).toImage()
        if image.isNull():
            return []
        ratio = image.width() / max(1.0, strip["w"])
        h = image.height()
        bg = image.pixelColor(image.width() - 2, 2)  # the far end of the bar is empty
        def busy(px):
            for py in range(int(h * 0.25), int(h * 0.75), 2):
                c = image.pixelColor(px, py)
                if abs(c.red() - bg.red()) + abs(c.green() - bg.green()) + abs(c.blue() - bg.blue()) > 90:
                    return True
            return False
        spots, run_start, gap = [], None, 0
        for px in range(image.width() + 4):
            if px < image.width() and busy(px):
                if run_start is None:
                    run_start = px
                gap = 0
            elif run_start is not None:
                gap += 1
                if gap > 3:
                    width = (px - gap) - run_start + 1
                    if h * 0.3 <= width <= h * 1.0:
                        centre = (run_start + width / 2) / ratio
                        spots.append(main.slice["offset"] + strip["x"] + centre - main.geometry().x())
                    run_start, gap = None, 0
        return spots

    def _grab_icons(self):
        """Copy the icons the foxes just dug up (a picture only), shrunk so they look pixelated."""
        main = self.main_desktop()
        while self.world.grab_requests and self.taskbar_strip and main is not None:
            key, x = self.world.grab_requests.pop(0)
            strip = self.taskbar_strip
            size = int(strip["h"] * 0.62)
            gx = int(main.geometry().x() + x - main.slice["offset"] - size / 2)
            gy = int(strip["y"] + (strip["h"] - size) / 2)
            picture = main.screen_.grabWindow(0, gx, gy, size, size)
            from pet.items import Treasure
            small = picture.scaled(Treasure.SIZE, Treasure.SIZE, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            s = self.world.scale
            self.world.images[key] = small.scaled(Treasure.SIZE * s, Treasure.SIZE * s, Qt.IgnoreAspectRatio,
                                                  Qt.FastTransformation)
        self.world.grab_requests.clear()

    # -- desktop folders (on the main monitor) -------------------------------------------------------------

    def look_for_folders(self):
        """Where the folder icons on the main monitor are, along the strip (none if mischief is off)."""
        main = self.main_desktop()
        if not desktop_icons.ON_WINDOWS or main is None or not self.world.mischief("folders") or self.movers:
            if not self.movers:
                self.world.folder_spots = []
            return
        ratio = main.screen_.devicePixelRatio()
        screen = main.screen_.geometry()
        spots = []
        for icon in desktop_icons.folders():
            # physical pixels -> Qt's: the main monitor starts at 0, 0 in both
            box = QRect(int(icon["left"] / ratio), int(icon["top"] / ratio), int(icon["width"] / ratio),
                        int(icon["height"] / ratio))
            if not main.geometry().contains(box.center()) or not screen.contains(box):
                continue
            x, y = self.to_world(QPoint(box.center().x(), box.bottom()))
            if x > -9999:
                spots.append({"name": icon["name"], "x": x, "y": y, "w": float(box.width()),
                              "h": float(box.height()), "home": icon["place"],
                              "left": float(main.slice["offset"]), "right": float(main.slice["offset"] + main.width())})
        self.world.folder_spots = spots

    def _move_folders(self):
        """Move the real folder icons to keep up with the foxes (only the latest place for each)."""
        main = self.main_desktop()
        latest = {}
        for action, name, x, y, w, h in self.world.folder_requests:
            latest[name] = (action, x, y, w, h)
        self.world.folder_requests.clear()
        if main is None or not desktop_icons.ON_WINDOWS:
            return
        ratio = main.screen_.devicePixelRatio()
        for name, (action, x, y, w, h) in latest.items():
            mover = self.movers.get(name)
            if mover is None:
                mover = self.movers[name] = desktop_icons.Mover(name)
                spot_home = next((f.home for f in self.world.of("folder") if f.name == name), None)
                if mover.ok and spot_home and name not in self.settings["folder_homes"]:
                    self.settings["folder_homes"][name] = list(spot_home)  # so it can be put back
                    save.store(self.settings)
            top_left = main.mapToGlobal(QPoint(int(x - w / 2 + main.dx), int(y - h + main.dy)))
            mover.move_box(top_left.x() * ratio, top_left.y() * ratio)
            if action == "drop":
                self.movers.pop(name, None)

    def put_folders_back(self):
        homes = dict(self.settings.get("folder_homes", {}))
        for folder in self.world.of("folder"):
            folder.let_go()
        self.world.folder_requests.clear()
        self.movers.clear()
        desktop_icons.put_back(homes)
        self.settings["folder_homes"] = {}
        save.store(self.settings)
        QTimer.singleShot(300, self.look_for_folders)

    # -- the loop --------------------------------------------------------------------------------------

    def tick(self):
        dt = self.clock.restart() / 1000
        self.elapsed += dt
        cursor = self.to_world(QCursor.pos())
        before = [d.area() for d in self.desktops]
        self.world.weather = self.weather.current()
        self.world.update(dt, cursor)
        if self.world.grab_requests:
            self._grab_icons()
        if self.world.screen_requests:
            self._handle_screen_requests()
        if self.world.folder_requests:
            self._move_folders()
        if self.dragging is not None and self.dragging.kind == "fox" and cursor[0] > -9999:
            self.dragging.x, self.dragging.y = cursor[0], cursor[1] + 22 * self.world.scale
        elif self.dragging is not None and getattr(self.dragging, "held", False) and cursor[0] > -9999:
            self.dragging.x, self.dragging.y = cursor  # a corn cob (or a ball) in your hand
            self.trail = [p for p in self.trail if self.elapsed - p[0] < 0.12] + [(self.elapsed, *cursor)]
        if self.world.dirty:
            self.world.dirty = False
            save.store(self.settings)
        for d, old in zip(self.desktops, before):
            if self.covers:
                d.update()
            else:
                d.update(old.united(d.area()))

    # -- the mouse (any monitor) -----------------------------------------------------------------------

    def pressed(self, x, y):
        thing = self.world.thing_at(x, y, draggable_only=True)
        if thing is not None:
            self.press = (thing, (x, y), thing.x)

    def moved(self, x, y, buttons):
        if self.press and self.dragging is None:
            thing, (sx, sy), _ = self.press
            if abs(x - sx) + abs(y - sy) > DRAG_START:
                self.dragging = thing
                if thing.kind == "pumpkin" and self.world.decos_in_season() and \
                        abs(y - sy) > abs(x - sx) and self.world.pick_pumpkin(thing) is not None:
                    thing = self.dragging = self.world.of("deco")[-1]  # lifted out of the patch: picked
                    self.press = (thing, (x, y), thing.x)
                if thing.kind == "fox" or getattr(thing, "is_cob", False) or getattr(thing, "is_ball", False) or \
                        getattr(thing, "is_deco", False):
                    thing.pick_up()
                    self.trail = []
        if self.dragging is not None and self.dragging.kind in DRAGGED_ALONG:
            thing, (sx, _), start_x = self.press
            thing.x = max(40.0, min(self.world.width - 40.0, start_x + x - sx))
        elif self.dragging is None and not buttons:
            # stroking a fox with the cursor is petting it
            thing = self.world.thing_at(x, y)
            if thing is not None and thing.kind == "fox" and self.elapsed - self.last_pet > 0.25:
                self.last_pet = self.elapsed
                thing.pet()

    def throw_speed(self):
        """(vx, vy) in pixels per second, from the last moment of the cursor's movement."""
        trail = getattr(self, "trail", [])
        if len(trail) < 2 or trail[-1][0] - trail[0][0] <= 0:
            return 0.0, 0.0
        (t0, x0, y0), (t1, x1, y1) = trail[0], trail[-1]
        return (x1 - x0) / (t1 - t0), (y1 - y0) / (t1 - t0)

    def released(self):
        if self.dragging is not None:
            if getattr(self.dragging, "is_ball", False) or getattr(self.dragging, "is_cob", False):
                self.dragging.throw(*self.throw_speed())  # how fast your hand was moving as you let go
            elif self.dragging.kind == "fox" or getattr(self.dragging, "is_deco", False):
                self.dragging.drop()
            elif self.dragging.kind in PLACED_ITEMS:
                self.world.keep_off_seams(self.dragging)  # dropped across two monitors: onto one of them
                self.settings["items"][self.dragging.variant]["x"] = round(self.dragging.x)
                save.store(self.settings)
                self.world.dropped(self.dragging)
            elif self.dragging.kind in ("pumpkin", "melon") and self.dragging.record is not None:
                self.world.keep_off_seams(self.dragging)
                self.dragging.record["x"] = round(self.dragging.x)
                save.store(self.settings)
        elif self.press is not None and self.press[0].kind == "fox":
            self.press[0].poke()
        elif self.press is not None:
            self.press[0].click()  # each item has its own reaction
        self.press = None
        self.dragging = None


class SkyWindow(QWidget):
    """The sun by day, the moon by night (in its phase), behind every other window: a small window kept at the
    bottom of the stack that clicks go straight through, moved along its arc across all the monitors."""

    def __init__(self, stage):
        super().__init__(None, Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnBottomHint |
                         Qt.WindowTransparentForInput | Qt.WindowDoesNotAcceptFocus | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.stage = stage
        self.frames = Frames()
        self.look = None  # (sprite, frame, facing)

    def zoom(self):
        return self.stage.world.scale + 1

    def place(self):
        """Put it where the sun or moon is now (hidden if neither is up, or it's switched off)."""
        world, settings = self.stage.world, self.stage.settings
        found = sky.placement(world.now(), settings) if settings.get("sky", True) else None
        desktops = self.stage.desktops
        if found is None or not desktops:
            self.hide()
            return
        body, across, up, frame, mirrored = found
        self.look = (body, frame, -1 if mirrored and body == "moon" else 1)
        meta = sprites.meta(body)
        w, h = meta["frame_width"] * self.zoom(), meta["frame_height"] * self.zoom()
        margin = w
        x = margin + across * max(1.0, world.width - 2 * margin)  # along the strip, across every monitor
        d = next((d for d in desktops if d.slice["offset"] <= x < d.slice["offset"] + d.width()), desktops[-1])
        horizon, top = d.height() * 0.62, d.height() * 0.08
        y = horizon - up * (horizon - top)
        corner = d.mapToGlobal(QPoint(int(x - d.slice["offset"] - w / 2), int(y - h / 2)))
        self.setGeometry(corner.x(), corner.y(), w, h)
        if not self.isVisible():
            self.show()
        self.lower()  # and stay behind everything
        self.update()

    def paintEvent(self, event):
        if self.look is None:
            return
        body, frame, facing = self.look
        painter = QPainter(self)
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.fillRect(self.rect(), Qt.transparent)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        if body == "sun":
            frame = int(self.stage.elapsed / 0.9) % 2  # the rays shimmer
        painter.drawPixmap(0, 0, self.frames.get(body, frame, self.zoom(), facing))
        painter.end()


class Desktop(QWidget):
    """One monitor's see-through window, showing its slice of the strip."""

    def __init__(self, stage, screen, slice_):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setMouseTracking(True)
        self.stage, self.world, self.screen_, self.slice = stage, stage.world, screen, slice_
        self.setScreen(screen)
        self.setGeometry(QRect(slice_["x"], slice_["y"], slice_["w"], slice_["h"]))
        self.dx = -slice_["offset"]                    # strip x -> this window's x
        self.dy = (slice_["h"] - 2) - self.world.ground  # the world's ground -> this monitor's taskbar edge

    def to_world(self, px, py):
        return float(px - self.dx), float(py - self.dy)

    def area(self):
        """The part of this window everything covers (only that part is redrawn)."""
        area = QRect()
        for thing in self.world.things:
            if thing.kind == "folder":
                continue  # the real icon is drawn by Windows
            left, top, w, h = thing.rect()
            r = QRect(int(left + self.dx) - 2, int(top + self.dy) - 2, int(w) + 4, int(h) + 4)
            if r.intersects(self.rect()):
                area = area.united(r)
        return area

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.fillRect(event.rect(), Qt.transparent)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        view = self.rect()
        out = {m.key for m in self.world.of("message") if m.state != "home"}
        for key, (band, colour, _, _) in getattr(self.stage, "covers", {}).items():  # gaps where messages were stolen
            if key not in out:
                continue  # not pulled out yet: nothing to hide
            local = QRect(self.mapFromGlobal(band.topLeft()), band.size())
            if local.intersects(view):
                painter.fillRect(local, colour)
        for thing in self.world.drawing_order():
            if thing.kind == "folder":
                continue  # the real icon is drawn by Windows
            left, top, w, h = thing.rect()
            x, y = int(round(left + self.dx)), int(round(top + self.dy))
            if not view.intersects(QRect(x, y, int(w), int(h))):
                continue  # on another monitor
            if thing.kind in ("treasure", "message"):
                pixmap = self.world.images.get(thing.key)
                if pixmap is None:
                    continue
                if pixmap.width() != int(w):  # partly chewed: smaller
                    pixmap = pixmap.scaled(int(w), int(h), Qt.IgnoreAspectRatio, Qt.FastTransformation)
            else:
                pixmap = self.stage.frames.get(thing.anim.name, thing.anim.frame, self.world.scale, thing.facing)
            painter.setOpacity(max(0.0, min(1.0, thing.alpha)))
            painter.drawPixmap(x, y, pixmap)
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            where = self.mapToGlobal(event.position().toPoint())
            for key, (band, _, _, _) in list(getattr(self.stage, "covers", {}).items()):
                if band.contains(where):
                    self.world.send_message_home(key)  # clicked the gap: the message flies back
                    return
            self.stage.pressed(*self.to_world(event.position().x(), event.position().y()))

    def mouseMoveEvent(self, event):
        x, y = self.to_world(event.position().x(), event.position().y())
        self.stage.moved(x, y, bool(event.buttons()))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.stage.released()


class ToyBoxWindow(QWidget):
    """A small window listing every fox and item with a checkbox: tick what you want on the desktop.
    Opens when you click the fox icon in the tray."""

    def __init__(self, toybox):
        super().__init__(None, Qt.Tool | Qt.WindowStaysOnTopHint)
        self.toybox = toybox
        self.setWindowTitle("Toy Box")
        self.setWindowIcon(toybox.tray.icon())
        self.layout_ = QVBoxLayout(self)
        self.boxes = {}  # (kind, name) -> its checkboxes (an item out in two seasons is on both seasons' tabs)
        foxes = QGroupBox("Foxes")
        fox_layout = QVBoxLayout(foxes)
        for palette, label in (("orange", "Orange fox"), ("grey", "Grey fox")):
            box = QCheckBox(label)
            box.toggled.connect(lambda on, p=palette: toybox._set_fox(p, on))
            fox_layout.addWidget(box)
            self.boxes[("fox", palette)] = [box]
        self.layout_.addWidget(foxes)
        # the items, on tabs: the ones out all year, then each season's
        self.tabs = QTabWidget()
        self.tabs.setUsesScrollButtons(False)  # wide enough to show every tab
        self.tab_of = {}
        for key, title in (("all", "All year"),) + tuple((s, s.title()) for s in seasons.SEASONS):
            page = QWidget()
            page_layout = QVBoxLayout(page)
            names = [n for n, item in seasons.ITEMS.items()
                     if (key == "all") == (len(item["seasons"]) == len(seasons.SEASONS))
                     and (key == "all" or key in item["seasons"])]
            for name in sorted(names, key=lambda n: seasons.ITEMS[n]["label"]):
                box = QCheckBox(seasons.ITEMS[name]["label"])
                box.toggled.connect(lambda on, n=name: toybox._set_item(n, on))
                page_layout.addWidget(box)
                self.boxes.setdefault(("item", name), []).append(box)
            page_layout.addStretch(1)
            self.tab_of[key] = self.tabs.addTab(page, title)
        self.layout_.addWidget(self.tabs)
        mischief = QGroupBox("Mischief")
        mischief_layout = QVBoxLayout(mischief)
        for key, label in (("discord", "Steal Discord messages (and put them back)"),
                           ("treasure", "Dig up taskbar icons"),
                           ("folders", "Move folders about on the desktop")):
            box = QCheckBox(label)
            box.toggled.connect(lambda on, k=key: toybox._set_mischief(k, on))
            mischief_layout.addWidget(box)
            self.boxes[("mischief", key)] = [box]
        self.layout_.addWidget(mischief)
        self.note = QLabel()
        self.note.setWordWrap(True)
        self.layout_.addWidget(self.note)
        close = QPushButton("Close")
        close.clicked.connect(self.hide)
        self.layout_.addWidget(close)

    def refresh(self):
        """Show the current settings (without firing the checkboxes' handlers)."""
        settings, season = self.toybox.settings, self.toybox.world.season
        for (kind, name), boxes in self.boxes.items():
            if kind == "fox":
                on = bool(settings["foxes"].get(name))
            elif kind == "mischief":
                on = bool(settings.get("mischief", {}).get(name, True))
            else:
                on = bool(settings["items"].get(name, {}).get("out"))
            for box in boxes:
                box.blockSignals(True)
                box.setChecked(on)
                box.blockSignals(False)
        for key, index in self.tab_of.items():
            title = "All year" if key == "all" else key.title()
            self.tabs.setTabText(index, f"{title} (now)" if key == season else title)
        self.note.setText(f"It's {season} now. Things ticked on another season's tab come out when their season "
                          f"does.")

    def open(self):
        self.refresh()
        self.tabs.setCurrentIndex(self.tab_of[self.toybox.world.season])  # this season's things first
        self.adjustSize()
        self.show()
        self.raise_()
        self.activateWindow()


class ToyBox:
    """The tray icon's menu: which foxes and items are out, the season, pause and quit."""

    def __init__(self, app, desktop):
        self.app, self.desktop = app, desktop
        self.world, self.settings = desktop.world, desktop.settings
        icon = QIcon(str(sprites.SPRITE_DIR / "tray_icon.png"))
        self.tray = QSystemTrayIcon(icon)
        self.tray.setToolTip(f"Pixel Fox {__version__}")
        self.menu = QMenu()
        self.menu.aboutToShow.connect(self.build)
        self.tray.setContextMenu(self.menu)
        self.tray.show()
        self.window = ToyBoxWindow(self)
        self.tray.activated.connect(self._clicked)

    def _clicked(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):  # a left click
            self.window.open()

    def build(self):
        m = self.menu
        m.clear()
        m.addAction("Open the toy box...", self.window.open)
        m.addSection("Foxes")
        for palette, label in (("orange", "Orange fox"), ("grey", "Grey fox")):
            self._check(m, label, self.settings["foxes"].get(palette, False),
                        lambda on, p=palette: self._set_fox(p, on))
        items = seasons.items_for(self.world.season)
        all_year = [n for n in items if len(seasons.ITEMS[n]["seasons"]) == len(seasons.SEASONS)]
        for title, names in (("All year", all_year),
                             (f"This season ({self.world.season.title()})", [n for n in items if n not in all_year])):
            m.addSection(title)
            for name in sorted(names, key=lambda n: seasons.ITEMS[n]["label"]):
                item = self.settings["items"].setdefault(name, {"out": False, "x": None})
                self._check(m, seasons.ITEMS[name]["label"], item.get("out", False),
                            lambda on, n=name: self._set_item(n, on))
        m.addSection("Things to do")
        if self.world.tree() is not None and self.world.season == "autumn":
            m.addAction("Shake down an acorn", lambda: self.world.drop_acorn(self.world.tree()))
        if self.world.season == "winter":
            snow = m.addAction("Snow on the oak")
            snow.setCheckable(True)
            snow.setChecked(self.world.snowy)
            snow.toggled.connect(self._set_snow)
        if self.world.of("pumpkin"):
            m.addAction("Plant new pumpkins", self._replant)
        if self.world.decos_in_season():
            m.addAction("Add a pumpkin (to decorate with)", lambda: self.world.add_deco())
            m.addAction("Add a jack-o'-lantern", lambda: self.world.add_deco(jack=True))
            if self.world.of("deco"):
                m.addAction("Clear away the decorating pumpkins", self.world.clear_decos)
        if self.world.of("corn"):
            m.addAction("Plant new corn", self._replant_corn)
        if self.world.of("melon"):
            m.addAction("Plant new watermelons", self._replant_melons)
        if self.world.of("crop"):
            m.addAction("Replant the garden", self._replant_crops)
        if self.world.taskbar_spots:
            m.addAction("Dig up a taskbar treasure", self._dig)
        if self.world.folder_spots and self.world.mischief("folders"):
            m.addAction("Move a desktop folder", self._move_a_folder)
        if self.settings.get("folder_homes"):
            m.addAction("Put the desktop folders back", self.desktop.put_folders_back)
        m.addAction("Zoomies!", self._zoomies)
        m.addAction("Make it blustery", lambda: self.world.blustery())
        m.addAction("Make it rain", lambda: self.world.make_it("rain"))
        m.addAction("Make it snow", lambda: self.world.make_it("snow"))
        m.addAction("Steal a Discord message", self._steal_discord)
        visit = m.addMenu("Invite a visitor")
        for kind in seasons.VISITORS.get(self.world.season, ()) + ("owl",):
            label = {"jay": "Blue jay", "woolly": "Woolly bear caterpillar", "migrants": "Geese flying south",
                     "geese": "Geese stopping by to honk", "squirrel": "Squirrel",
                     "turkeys": "Wild turkeys", "crows": "Crows", "junebug": "June beetle",
                     "ladybug": "Ladybug", "cicada": "Cicada", "butterflies": "Butterflies",
                     "songbirds": "Songbirds", "owl": "Owl (it usually comes at night)"}.get(kind, kind.title())
            visit.addAction(label, lambda k=kind: self.world.invite_visitor(k))

        m.addSeparator()
        season_menu = m.addMenu("Season")
        group = QActionGroup(season_menu)
        current = self.settings.get("season", "auto")
        auto_label = f"Automatic (now {seasons.season_for(self.world.now().date()).title()})"
        for key, label in (("auto", auto_label), ("winter", "Winter"), ("spring", "Spring"), ("summer", "Summer"),
                           ("autumn", "Autumn")):
            action = season_menu.addAction(label, lambda k=key: self._set_season(k))
            action.setCheckable(True)
            action.setChecked(current == key)
            group.addAction(action)
        self._check(m, self._weather_label(), self.settings.get("weather", True), self._set_weather)
        self._check(m, "Sun and moon in the sky", self.settings.get("sky", True), self._set_sky)
        size_menu = m.addMenu("Size")
        sizes = QActionGroup(size_menu)
        for value in (1, 2, 3):
            action = size_menu.addAction(f"{value}x", lambda v=value: self._set_scale(v))
            action.setCheckable(True)
            action.setChecked(self.world.scale == value)
            sizes.addAction(action)
        self._check(m, "Pause", self.world.paused, self._set_paused)
        m.addSeparator()
        m.addAction("Quit", self.quit)

    def _check(self, menu, label, checked, on_toggle):
        action = QAction(label, menu)
        action.setCheckable(True)
        action.setChecked(checked)
        action.toggled.connect(on_toggle)
        menu.addAction(action)
        return action

    def _changed(self):
        save.store(self.settings)
        self.world.rebuild()
        self.desktop.update()
        if self.window.isVisible():
            self.window.refresh()

    def _set_mischief(self, key, on):
        self.settings.setdefault("mischief", {})[key] = on
        save.store(self.settings)
        if key == "discord" and not on:
            self.world.discord_spot = None

    def _set_fox(self, palette, on):
        self.settings["foxes"][palette] = on
        self._changed()

    def _set_item(self, name, on):
        self.settings["items"].setdefault(name, {"out": on, "x": None})["out"] = on
        self._changed()

    def _steal_discord(self):
        """Look for a Discord message now and send a fox after it (if one is showing)."""
        self.desktop.look_for_discord()
        foxes = [f for f in self.world.of("fox") if not f.held and not f.asleep]
        if self.world.discord_spot is None:
            self.tray.showMessage("Pixel Fox", "No Discord message in view to steal (is Discord open and visible?)")
        elif foxes:
            self.world.steal_message(min(foxes, key=lambda f: abs(f.x - self.world.discord_spot["x"])))

    def _zoomies(self):
        foxes = [f for f in self.world.of("fox") if not f.held]
        if foxes:
            fox = self.world.rng.choice(foxes)
            fox.do(*fox._zoomies())

    def _dig(self):
        foxes = [f for f in self.world.of("fox") if not f.held]
        if foxes:
            self.world.dig_for_treasure(self.world.rng.choice(foxes))

    def _replant_corn(self):
        self.world.plant_corn(replant=True)
        save.store(self.settings)

    def _replant_melons(self):
        self.world.grow_melons(replant=True)
        save.store(self.settings)

    def _replant_crops(self):
        for crop in list(self.world.of("crop")):
            self.world.plant_crop(crop.variant, replant=True)
        save.store(self.settings)

    def _set_sky(self, on):
        self.settings["sky"] = bool(on)
        save.store(self.settings)
        self.desktop.sky.place()

    def _weather_label(self):
        report = self.desktop.weather.current() if self.settings.get("weather", True) else None
        now = {None: "", "rain": " (raining now)", "snow": " (snowing now)"}[report.falling if report else None]
        return "Local weather (rain and snow)" + now

    def _set_weather(self, on):
        self.settings["weather"] = bool(on)
        save.store(self.settings)
        if on:
            self.desktop.weather.refresh()

    def _set_snow(self, on):
        self.settings["snow"] = bool(on)
        save.store(self.settings)

    def _move_a_folder(self):
        foxes = [f for f in self.world.of("fox") if not f.held and f.dragging_folder is None]
        if foxes and not self.world.of("folder") and self.world.folder_spots:
            fox = self.world.rng.choice(foxes)
            spot = min(self.world.folder_spots, key=lambda f: abs(f["x"] - fox.x))
            self.world.move_folder(fox, spot, by_itself=False)

    def _replant(self):
        self.world.grow_pumpkins(replant=True)
        save.store(self.settings)

    def _set_season(self, key):
        self.settings["season"] = key
        self._changed()

    def _set_scale(self, value):
        self.settings["scale"] = value
        self.world.scale = value
        self._changed()

    def _set_paused(self, on):
        self.world.paused = on

    def quit(self):
        tree = self.world.tree()
        if tree is not None:
            self.settings["items"][tree.variant]["x"] = round(tree.x)
        save.store(self.settings)
        self.tray.hide()
        self.app.quit()

