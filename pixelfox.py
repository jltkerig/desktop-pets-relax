"""Pixel Fox: desktop pets. Start with start.ps1 (or: pythonw pixelfox.py)."""
import sys

from PySide6.QtCore import QLockFile
from PySide6.QtWidgets import QApplication

from pet import save, screens
from pet.view import Stage, ToyBox
from pet.world import World


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    save.USER_DIR.mkdir(parents=True, exist_ok=True)
    lock = QLockFile(str(save.USER_DIR / "pixelfox.lock"))
    if not lock.tryLock(100):
        return 0  # already running
    settings = save.load()
    areas = [(a.x(), a.y(), a.width(), a.height()) for a in (s.availableGeometry() for s in app.screens())]
    slices, width, height = screens.layout(areas)
    world = World(width, height, settings, seams=[s["offset"] for s in slices[1:]])  # one strip across every monitor
    stage = Stage(world, settings)
    toybox = ToyBox(app, stage)  # noqa: F841  (kept alive by this name)
    code = app.exec()
    lock.unlock()
    return code


if __name__ == "__main__":
    sys.exit(main())
