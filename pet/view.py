"""The see-through window the pets live in, and the tray menu (the toy box).

The window covers the desktop above the taskbar. It is transparent, so clicks on empty pixels go straight
to the desktop; only the foxes, the tree and the other things catch the mouse.
"""
import json
from pathlib import Path

from PySide6.QtCore import QElapsedTimer, QPoint, QProcess, QRect, Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup, QCursor, QIcon, QPainter, QPixmap, QTransform
from PySide6.QtWidgets import (QApplication, QCheckBox, QGroupBox, QLabel, QMenu, QPushButton, QSystemTrayIcon,
                               QVBoxLayout, QWidget)

from pet import save, seasons, sprites

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


class Desktop(QWidget):
    def __init__(self, world, settings, geometry):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setMouseTracking(True)
        self.setGeometry(geometry)
        self.world, self.settings = world, settings
        self.frames = Frames()
        self.press = None       # (thing, press point, thing's start x/y)
        self.dragging = None
        self.last_pet = 0.0
        self.clock = QElapsedTimer()
        self.clock.start()
        self.elapsed = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(FRAME_MS)
        # where the taskbar icons are (for digging up "treasure"); checked now and every few minutes
        self.taskbar_strip = None
        self.finder = QProcess(self)
        self.finder.finished.connect(self._taskbar_found)
        self.find_taskbar()
        self.taskbar_timer = QTimer(self)
        self.taskbar_timer.timeout.connect(self.find_taskbar)
        self.taskbar_timer.start(TASKBAR_REFRESH_MS)

    # -- the taskbar icons ------------------------------------------------------------------------------

    def find_taskbar(self):
        if self.finder.state() == QProcess.NotRunning:
            self.finder.start("powershell", ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(TASKBAR_SCRIPT)])

    def _taskbar_found(self):
        try:
            strip = json.loads(bytes(self.finder.readAllStandardOutput()).decode("utf-8", "replace") or "{}")
            ratio = self.screen().devicePixelRatio()
            strip = {k: strip[k] / ratio for k in ("x", "y", "w", "h")}
        except (ValueError, KeyError, TypeError):
            return
        if strip["w"] < 20 or strip["h"] < 10:
            return
        self.taskbar_strip = strip
        self.world.taskbar_spots = self._icon_spots(strip)

    def _icon_spots(self, strip):
        """The x (in this window) of the centre of each icon in the strip.

        Columns where the middle of the bar differs from the plain bar colour are part of an icon; runs of
        such columns about an icon wide are icons.
        """
        image = self.screen().grabWindow(0, int(strip["x"]), int(strip["y"]), int(strip["w"]), int(strip["h"])).toImage()
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
                        spots.append(strip["x"] + centre - self.geometry().x())
                    run_start, gap = None, 0
        return spots

    def _grab_icons(self):
        """Copy the icons the foxes just dug up (a picture only), shrunk so they look pixelated."""
        while self.world.grab_requests and self.taskbar_strip:
            key, x = self.world.grab_requests.pop(0)
            strip = self.taskbar_strip
            size = int(strip["h"] * 0.62)
            gx = int(self.geometry().x() + x - size / 2)
            gy = int(strip["y"] + (strip["h"] - size) / 2)
            picture = self.screen().grabWindow(0, gx, gy, size, size)
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
        local = self.mapFromGlobal(QCursor.pos())
        before = self._area()
        self.world.update(dt, (float(local.x()), float(local.y())))
        if self.world.grab_requests:
            self._grab_icons()
        if self.dragging is not None and self.dragging.kind == "fox":
            self.dragging.x, self.dragging.y = float(local.x()), float(local.y()) + 22 * self.world.scale
        if self.world.dirty:
            self.world.dirty = False
            save.store(self.settings)
        after = self._area()
        self.update(before.united(after))

    def _area(self):
        """The screen area everything covers (only that part is redrawn)."""
        area = QRect()
        for thing in self.world.things:
            left, top, w, h = thing.rect()
            area = area.united(QRect(int(left) - 2, int(top) - 2, int(w) + 4, int(h) + 4))
        return area

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.fillRect(event.rect(), Qt.transparent)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        for thing in self.world.drawing_order():
            left, top, _, _ = thing.rect()
            if thing.kind == "treasure":
                pixmap = self.world.images.get(thing.key)
                if pixmap is None:
                    continue
            else:
                pixmap = self.frames.get(thing.anim.name, thing.anim.frame, self.world.scale, thing.facing)
            painter.setOpacity(max(0.0, min(1.0, thing.alpha)))
            painter.drawPixmap(int(round(left)), int(round(top)), pixmap)
        painter.end()

    # -- the mouse -------------------------------------------------------------------------------------

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        p = event.position()
        thing = self.world.thing_at(p.x(), p.y(), draggable_only=True)
        if thing is not None:
            self.press = (thing, QPoint(int(p.x()), int(p.y())), thing.x)

    def mouseMoveEvent(self, event):
        p = event.position()
        if self.press and self.dragging is None:
            thing, start, _ = self.press
            if (QPoint(int(p.x()), int(p.y())) - start).manhattanLength() > DRAG_START:
                self.dragging = thing
                if thing.kind == "fox":
                    thing.pick_up()
        if self.dragging is not None and self.dragging.kind in ("tree", "pumpkin", "prop", "corn", "den", "climb"):
            thing, start, start_x = self.press
            thing.x = max(40.0, min(self.world.width - 40.0, start_x + p.x() - start.x()))
        elif self.dragging is None and not event.buttons():
            # stroking a fox with the cursor is petting it
            thing = self.world.thing_at(p.x(), p.y())
            if thing is not None and thing.kind == "fox" and self.elapsed - self.last_pet > 0.25:
                self.last_pet = self.elapsed
                thing.pet()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        if self.dragging is not None:
            if self.dragging.kind == "fox":
                self.dragging.drop()
            elif self.dragging.kind in ("tree", "prop", "corn", "den", "climb"):
                self.settings["items"][self.dragging.variant]["x"] = round(self.dragging.x)
                save.store(self.settings)
            elif self.dragging.kind == "pumpkin" and self.dragging.record is not None:
                self.dragging.record["x"] = round(self.dragging.x)
                save.store(self.settings)
        elif self.press is not None and self.press[0].kind == "fox":
            self.press[0].poke()
        elif self.press is not None:
            self.press[0].click()  # each item has its own reaction
        self.press = None
        self.dragging = None


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
        self.tray.setToolTip("Pixel Fox")
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
        if self.world.tree() is not None:
            m.addAction("Shake down an acorn", lambda: self.world.drop_acorn(self.world.tree()))
        if self.world.of("pumpkin"):
            m.addAction("Plant new pumpkins", self._replant)
        if self.world.of("corn"):
            m.addAction("Plant new corn", self._replant_corn)
        if self.world.taskbar_spots:
            m.addAction("Dig up a taskbar treasure", self._dig)
        m.addAction("Zoomies!", self._zoomies)
        visit = m.addMenu("Invite a visitor")
        for kind in seasons.VISITORS.get(self.world.season, ()):
            label = {"jay": "Blue jay", "woolly": "Woolly bear caterpillar", "migrants": "Geese flying south",
                     "geese": "Geese stopping by to honk", "squirrel": "Squirrel"}.get(kind, kind.title())
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

    def _set_fox(self, palette, on):
        self.settings["foxes"][palette] = on
        self._changed()

    def _set_item(self, name, on):
        self.settings["items"].setdefault(name, {"out": on, "x": None})["out"] = on
        self._changed()

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


def work_area():
    screen = QApplication.primaryScreen()
    return screen.availableGeometry()
