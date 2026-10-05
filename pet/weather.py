"""Is it raining or snowing where you are? Asked of Open-Meteo (free, no account or key), every half hour, in
the background. Only a rough location is sent: the city daylight.py picked from your time zone (or the one you
set in settings["location"]), rounded to a tenth of a degree. If there's no internet, or anything goes wrong,
there's simply no weather report and Pixel Fox carries on as before. Turn it off with settings["weather"] =
false (the tray menu's "Local weather").

No Qt in here, so it can be tested; the fetching is done by a plain thread.
"""
import datetime
import json
import threading
import urllib.request

URL = ("https://api.open-meteo.com/v1/forecast?latitude={lat:.1f}&longitude={lon:.1f}"
       "&current=weather_code,precipitation,rain,showers,snowfall,snow_depth,temperature_2m")
EVERY = 30 * 60        # seconds between reports
STALE = 3 * 60 * 60    # a report older than this is ignored (the computer slept, or went offline)

# WMO weather codes, as Open-Meteo gives them
SNOW_CODES = {71, 73, 75, 77, 85, 86}
RAIN_CODES = {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99}
HEAVY_CODES = {65, 67, 75, 82, 86, 95, 96, 99}


class Report:
    """What the weather's doing. falling: None, "rain" or "snow"; heavy: a downpour or a blizzard;
    snow_on_ground: there's snow lying about (so a winter day is a snowy one)."""

    def __init__(self, falling=None, heavy=False, snow_on_ground=False, when=None):
        self.falling, self.heavy, self.snow_on_ground = falling, heavy, snow_on_ground
        self.when = when or datetime.datetime.now()

    def __repr__(self):
        return f"Report({self.falling!r}, heavy={self.heavy}, snow_on_ground={self.snow_on_ground})"


def parse(data, when=None):
    """An Open-Meteo answer (the decoded JSON) -> a Report, or None if it doesn't make sense."""
    try:
        now = data["current"]
        code = int(now.get("weather_code") or 0)
        snowfall = float(now.get("snowfall") or 0)     # cm in the last hour
        wet = float(now.get("rain") or 0) + float(now.get("showers") or 0)  # mm
        depth = float(now.get("snow_depth") or 0)      # metres
    except (KeyError, TypeError, ValueError, AttributeError):
        return None
    if code in SNOW_CODES or snowfall > 0:
        falling = "snow"
    elif code in RAIN_CODES or wet > 0:
        falling = "rain"
    else:
        falling = None
    heavy = falling is not None and (code in HEAVY_CODES or wet >= 4 or snowfall >= 2)
    return Report(falling, heavy, depth >= 0.01 or falling == "snow", when)


def where(settings):
    """(lat, lon) to ask about: the location you set, or the city picked from your time zone. None if neither."""
    loc = (settings or {}).get("location") or {}
    if loc.get("lat") is not None and loc.get("lon") is not None:
        return float(loc["lat"]), float(loc["lon"])
    from pet import daylight
    observer, _ = daylight._place()
    if observer is None:
        return None
    return observer.latitude, observer.longitude


def fetch(lat, lon, opener=None, timeout=15):
    """Ask Open-Meteo now. A Report, or None if it couldn't be had."""
    opener = opener or urllib.request.urlopen
    try:
        request = urllib.request.Request(URL.format(lat=lat, lon=lon), headers={"User-Agent": "PixelFox"})
        with opener(request, timeout=timeout) as answer:
            return parse(json.loads(answer.read().decode("utf-8")))
    except Exception:
        return None


class Watcher:
    """Keeps a fresh weather report in .latest, fetched on a background thread every half hour."""

    def __init__(self, settings, fetcher=None):
        self.settings, self.fetcher = settings, fetcher
        self.latest = None
        self._wake = threading.Event()
        self._stop = False
        self._thread = None

    def start(self):
        if self._thread is None:
            self._thread = threading.Thread(target=self._run, name="pixelfox-weather", daemon=True)
            self._thread.start()
        return self

    def stop(self):
        self._stop = True
        self._wake.set()

    def refresh(self):
        """Fetch again now (say, weather was just switched back on)."""
        self._wake.set()

    def check(self):
        if not self.settings.get("weather", True):
            return
        place = where(self.settings)
        if place is None:
            return
        report = (self.fetcher or fetch)(*place)
        if report is not None:
            self.latest = report

    def _run(self):
        while not self._stop:
            self.check()
            self._wake.wait(EVERY)
            self._wake.clear()

    def current(self, now=None):
        """The latest report if it's fresh and weather is on, else None."""
        report = self.latest
        if report is None or not self.settings.get("weather", True):
            return None
        if ((now or datetime.datetime.now()) - report.when).total_seconds() > STALE:
            return None
        return report
