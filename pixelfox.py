"""Pixel Fox: desktop pets. Start with start.ps1 (or: pythonw pixelfox.py)."""
import sys

from PySide6.QtCore import QLockFile
from PySide6.QtWidgets import QApplication

from pet import save
from pet.view import Desktop, ToyBox, work_area
from pet.world import World


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    save.USER_DIR.mkdir(parents=True, exist_ok=True)
    lock = QLockFile(str(save.USER_DIR / "pixelfox.lock"))
    if not lock.tryLock(100):
        return 0  # already running
    settings = save.load()
    area = work_area()
    world = World(area.width(), area.height(), settings)
    desktop = Desktop(world, settings, area)
    desktop.show()
    toybox = ToyBox(app, desktop)  # noqa: F841  (kept alive by this name)
    code = app.exec()
    lock.unlock()
    return code


if __name__ == "__main__":
    sys.exit(main())
