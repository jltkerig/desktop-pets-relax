"""The see-through window the pets live in, and the tray menu (the toy box).

The window covers the desktop above the taskbar. It is transparent, so clicks on empty pixels go straight
to the desktop; only the foxes, the tree and the other things catch the mouse.
"""
import json
from pathlib import Path

from PySide6.QtCore import QElapsedTimer, QPoint, QProcess, QRect, Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup, QColor, QCursor, QIcon, QPainter, QPixmap, QTransform
from PySide6.QtWidgets import (QApplication, QCheckBox, QGroupBox, QLabel, QMenu, QPushButton, QSystemTrayIcon,
                               QVBoxLayout, QWidget)

from pet import __version__, discord, save, screens, seasons, sprites

FRAME_MS = 33
TASKBAR_SCRIPT = Path(__file__).resolve().parent / "taskbar_buttons.ps1"
TASKBAR_REFRESH_MS = 3 * 60 * 1000
DRAG_START = 6  # pixels the mouse must move before a press becomes a drag


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


class Stage:
    """Runs the pets across every monitor: one see-through window per monitor, all showing slices of the
    same world. Notices monitors being plugged in, unplugged or rearranged, and rebuilds."""

    def __init__(self, world, settings):
        self.world, self.settings = world, settings
        self.frames = Frames()
        self.desktops = []
        self.press = None       # (thing, press point in the strip, thing's start x)
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
        # the chat column: past the server and channel lists, short of the member list and the typing box
        x0, x1 = left + 340, min(right - 260, left + 340 + 520)
        if x1 - x0 < 200:
            return
        for lift in (150, 210, 270, 330, 390):
            band = QRect(int(x0), int(bottom - lift - 46), int(x1 - x0), 46)
            corners = (band.topLeft(), band.topRight(), band.bottomLeft(), band.bottomRight(), band.center())
            if not all(discord.shows_at(hwnd, p.x(), p.y()) for p in corners):
                continue  # something covers this part of Discord
            logical = QRect(int(band.x() / ratio), int(band.y() / ratio), int(band.width() / ratio), int(band.height() / ratio))
            image = QApplication.primaryScreen().grabWindow(0, logical.x(), logical.y(), logical.width(), logical.height()).toImage()
            if image.isNull():
                continue
            bg = image.pixelColor(2, image.height() // 2)
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
        picture = QApplication.primaryScreen().grabWindow(0, band.x(), band.y(), band.width(), band.height())
        image = picture.toImage()
        cover = image.pixelColor(2, image.height() // 2)  # Discord's background colour, to hide the gap
        width = min(picture.width(), 150 * self.world.scale)
        small = picture.scaledToWidth(int(width), Qt.SmoothTransformation)
        self.world.images[key] = small
        for msg in self.world.of("message"):
            if msg.key == key:
                msg.size = (float(small.width()), float(small.height()))
        self.covers[key] = (band, cover, hwnd, bounds)
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

    # -- the loop --------------------------------------------------------------------------------------

    def tick(self):
        dt = self.clock.restart() / 1000
        self.elapsed += dt
        cursor = self.to_world(QCursor.pos())
        before = [d.area() for d in self.desktops]
        self.world.update(dt, cursor)
        if self.world.grab_requests:
            self._grab_icons()
        if self.world.screen_requests:
            self._handle_screen_requests()
        if self.dragging is not None and self.dragging.kind == "fox" and cursor[0] > -9999:
            self.dragging.x, self.dragging.y = cursor[0], cursor[1] + 22 * self.world.scale
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
                if thing.kind == "fox":
                    thing.pick_up()
        if self.dragging is not None and self.dragging.kind in ("tree", "pumpkin", "prop", "corn", "den", "climb"):
            thing, (sx, _), start_x = self.press
            thing.x = max(40.0, min(self.world.width - 40.0, start_x + x - sx))
        elif self.dragging is None and not buttons:
            # stroking a fox with the cursor is petting it
            thing = self.world.thing_at(x, y)
            if thing is not None and thing.kind == "fox" and self.elapsed - self.last_pet > 0.25:
                self.last_pet = self.elapsed
                thing.pet()

    def released(self):
        if self.dragging is not None:
            if self.dragging.kind == "fox":
                self.dragging.drop()
            elif self.dragging.kind in ("tree", "prop", "corn", "den", "climb"):
                self.world.keep_off_seams(self.dragging)  # dropped across two monitors: onto one of them
                self.settings["items"][self.dragging.variant]["x"] = round(self.dragging.x)
                save.store(self.settings)
                self.world.dropped(self.dragging)
            elif self.dragging.kind == "pumpkin" and self.dragging.record is not None:
                self.world.keep_off_seams(self.dragging)
                self.dragging.record["x"] = round(self.dragging.x)
                save.store(self.settings)
        elif self.press is not None and self.press[0].kind == "fox":
            self.press[0].poke()
        elif self.press is not None:
            self.press[0].click()  # each item has its own reaction
        self.press = None
        self.dragging = None


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
        for band, colour, _, _ in self.stage.covers.values():  # gaps where messages were "stolen" from
            local = QRect(self.mapFromGlobal(band.topLeft()), band.size())
            if local.intersects(view):
                painter.fillRect(local, colour)
        for thing in self.world.drawing_order():
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
            self.stage.pressed(*self.to_world(event.position().x(), event.position().y()))

    def mouseMoveEvent(self, event):
        x, y = self.to_world(event.position().x(), event.position().y())
        self.stage.moved(x, y, bool(event.buttons()))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.stage.released()


SEASON_WORDS = {("winter", "spring", "summer", "autumn"): "all year"}


class ToyBoxWindow(QWidget):
    """A small window listing every fox and item with a checkbox: tick what you want on the desktop.
    Opens when you click the fox icon in the tray."""

    def __init__(self, toybox):
        super().__init__(None, Qt.Tool | Qt.WindowStaysOnTopHint)
        self.toybox = toybox
        self.setWindowTitle("Toy Box")
        self.setWindowIcon(toybox.tray.icon())
        self.layout_ = QVBoxLayout(self)
        self.boxes = {}
        foxes = QGroupBox("Foxes")
        fox_layout = QVBoxLayout(foxes)
        for palette, label in (("orange", "Orange fox"), ("grey", "Grey fox")):
            box = QCheckBox(label)
            box.toggled.connect(lambda on, p=palette: toybox._set_fox(p, on))
            fox_layout.addWidget(box)
            self.boxes[("fox", palette)] = box
        self.layout_.addWidget(foxes)
        items = QGroupBox("On the desktop")
        item_layout = QVBoxLayout(items)
        for name, item in seasons.ITEMS.items():
            when = SEASON_WORDS.get(tuple(item["seasons"]), " and ".join(item["seasons"]))
            box = QCheckBox(f"{item['label']}  ({when})")
            box.toggled.connect(lambda on, n=name: toybox._set_item(n, on))
            item_layout.addWidget(box)
            self.boxes[("item", name)] = box
        self.layout_.addWidget(items)
        mischief = QGroupBox("Mischief")
        mischief_layout = QVBoxLayout(mischief)
        for key, label in (("discord", "Steal Discord messages (and put them back)"),
                           ("treasure", "Dig up taskbar icons")):
            box = QCheckBox(label)
            box.toggled.connect(lambda on, k=key: toybox._set_mischief(k, on))
            mischief_layout.addWidget(box)
            self.boxes[("mischief", key)] = box
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
        for (kind, name), box in self.boxes.items():
            box.blockSignals(True)
            if kind == "fox":
                box.setChecked(bool(settings["foxes"].get(name)))
            elif kind == "mischief":
                box.setChecked(bool(settings.get("mischief", {}).get(name, True)))
            else:
                box.setChecked(bool(settings["items"].get(name, {}).get("out")))
                box.setEnabled(True)
                in_season = season in seasons.ITEMS[name]["seasons"]
                font = box.font()
                font.setItalic(not in_season)  # ticked items from another season wait for their season
                box.setFont(font)
            box.blockSignals(False)
        self.note.setText(f"It's {season} now. Items in italics belong to another season: tick them and "
                          f"they'll come out when their season does.")

    def open(self):
        self.refresh()
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
        m.addSection(f"Toy box ({self.world.season.title()})")
        items = seasons.items_for(self.world.season)
        for name in items:
            item = self.settings["items"].setdefault(name, {"out": False, "x": None})
            self._check(m, seasons.ITEMS[name]["label"], item.get("out", False),
                        lambda on, n=name: self._set_item(n, on))
        if not items:
            disabled = m.addAction("Nothing for this season yet")
            disabled.setEnabled(False)
        if self.world.tree() is not None and self.world.season == "autumn":
            m.addAction("Shake down an acorn", lambda: self.world.drop_acorn(self.world.tree()))
        if self.world.season == "winter":
            snow = m.addAction("Snow on the oak")
            snow.setCheckable(True)
            snow.setChecked(self.world.snowy)
            snow.toggled.connect(self._set_snow)
        if self.world.of("pumpkin"):
            m.addAction("Plant new pumpkins", self._replant)
        if self.world.of("corn"):
            m.addAction("Plant new corn", self._replant_corn)
        if self.world.taskbar_spots:
            m.addAction("Dig up a taskbar treasure", self._dig)
        m.addAction("Zoomies!", self._zoomies)
        m.addAction("Make it blustery", lambda: self.world.blustery())
        m.addAction("Steal a Discord message", self._steal_discord)
        visit = m.addMenu("Invite a visitor")
        for kind in seasons.VISITORS.get(self.world.season, ()):
            label = {"jay": "Blue jay", "woolly": "Woolly bear caterpillar", "migrants": "Geese flying south",
                     "geese": "Geese stopping by to honk", "squirrel": "Squirrel",
                     "turkeys": "Wild turkeys", "crows": "Crows", "junebug": "June beetle",
                     "ladybug": "Ladybug", "cicada": "Cicada", "butterflies": "Butterflies",
                     "songbirds": "Songbirds"}.get(kind, kind.title())
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

    def _set_snow(self, on):
        self.settings["snow"] = bool(on)
        save.store(self.settings)

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

