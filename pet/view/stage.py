"""The Stage: runs the world, owns the monitor windows, the mouse (petting, dragging, throwing), the
taskbar icons, Discord, desktop folders, and the sun and moon."""
from PySide6.QtCore import QElapsedTimer, QPoint, QProcess, QRect, Qt, QTimer
from PySide6.QtGui import QCursor, QPixmap
from PySide6.QtWidgets import QApplication
import json

from pet import desktop_icons, discord, save, screens, weather
from .frames import DRAGGED_ALONG, DRAG_START, FRAME_MS, Frames, PLACED_ITEMS, TASKBAR_REFRESH_MS, TASKBAR_SCRIPT
from .discord_pics import AVATAR_COLUMN, background_colour, text_only
from .windows import Desktop, SkyWindow


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
