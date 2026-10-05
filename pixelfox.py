"""Pixel Fox: desktop pets. Start with start.ps1 (or: pythonw pixelfox.py).

    pythonw pixelfox.py --scr /s   the screen saver (what "Pixel Fox.scr" runs; /c settings, /p preview)
"""
import sys

from PySide6.QtCore import QLockFile
from PySide6.QtWidgets import QApplication

from pet import save, screens


def main():
    app = QApplication(sys.argv)
    save.USER_DIR.mkdir(parents=True, exist_ok=True)
    if "--scr" in sys.argv:
        return screen_saver(app, sys.argv[sys.argv.index("--scr") + 1:])
    from pet.view import Stage, ToyBox
    from pet.world import World
    app.setQuitOnLastWindowClosed(False)
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


def screen_saver(app, args):
    from pet import saver
    what = saver.mode(args)
    if what == "preview":
        return 0  # the little preview box in Windows' settings stays empty
    if what == "settings":
        saver.settings_box()
        return 0
    lock = QLockFile(str(save.USER_DIR / "screensaver.lock"))  # its own lock: it can run beside the desktop pets
    if not lock.tryLock(100):
        return 0  # already showing
    running = saver.Saver(app, save.load())  # noqa: F841  (kept alive by this name)
    code = app.exec()
    lock.unlock()
    return code


if __name__ == "__main__":
    sys.exit(main())
