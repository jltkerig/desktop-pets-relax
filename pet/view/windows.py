"""The windows: one see-through Desktop window per monitor (drawing the world, passing clicks on), and the
sun/moon window kept behind everything."""
from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QWidget

from pet import sky, sprites
from .frames import Frames


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
