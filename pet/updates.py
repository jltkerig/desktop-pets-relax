"""Is there a newer Pixel Fox on GitHub? Checked in the background now and then, for the tray menu, which then
offers to update and restart. (The update itself is done by update.ps1, run by start.ps1.) No Qt here."""
import re
import threading
import time
import urllib.request

URL = "https://raw.githubusercontent.com/jltkerig/desktop-pets-relax/main/pet/__init__.py"
EVERY = 3 * 60 * 60  # seconds between checks


def parse(text):
    """The version in a pet/__init__.py, as a tuple (1, 16, 1), or None."""
    m = re.search(r'__version__\s*=\s*"(\d+)\.(\d+)\.(\d+)"', text or "")
    return tuple(int(n) for n in m.groups()) if m else None


def fetch(timeout=10):
    """The newest version on GitHub, or None if it couldn't be had."""
    try:
        request = urllib.request.Request(f"{URL}?t={int(time.time())}", headers={"User-Agent": "PixelFox"})
        with urllib.request.urlopen(request, timeout=timeout) as answer:
            return parse(answer.read().decode("utf-8", "replace"))
    except Exception:
        return None


class Checker:
    """Keeps .newest up to date on a background thread."""

    def __init__(self, current, fetcher=None):
        self.current = parse(f'__version__ = "{current}"')
        self.fetcher = fetcher
        self.newest = None

    def start(self):
        threading.Thread(target=self._run, name="pixelfox-updates", daemon=True).start()
        return self

    def check(self):
        found = (self.fetcher or fetch)()
        if found:
            self.newest = found

    def _run(self):
        while True:
            self.check()
            time.sleep(EVERY)

    def available(self):
        """The newer version as text ("1.17.0") if there is one, else None."""
        if self.newest and self.current and self.newest > self.current:
            return ".".join(str(n) for n in self.newest)
        return None
