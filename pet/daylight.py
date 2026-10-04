"""Is it night, dawn, day or dusk where you are? Worked out offline from sunrise and sunset (the astral
library), for a place in your computer's time zone. No location leaves the computer.

The place: settings["location"] = {"lat": .., "lon": ..} if you set one; otherwise a city from astral's
built-in list whose time zone behaves like yours (same UTC offset in winter and in summer). If astral
isn't installed or nothing matches, simple clock hours are used instead.
"""
import datetime
from functools import lru_cache

PHASES = ("night", "dawn", "day", "dusk")
TWILIGHT = datetime.timedelta(minutes=45)  # dawn and dusk last this long either side of sunrise/sunset


def _local_zone():
    try:
        import tzlocal
        from zoneinfo import ZoneInfo
        return ZoneInfo(tzlocal.get_localzone_name())
    except Exception:
        return None


@lru_cache(maxsize=4)
def _place(lat=None, lon=None):
    """An astral Observer and time zone for your area, or (None, None)."""
    try:
        from astral import Observer, geocoder
        from zoneinfo import ZoneInfo
    except ImportError:
        return None, None
    zone = _local_zone()
    if lat is not None and lon is not None:
        return Observer(latitude=lat, longitude=lon), zone
    if zone is None:
        return None, None
    year = datetime.date.today().year
    probes = [datetime.datetime(year, 1, 15, 12), datetime.datetime(year, 7, 15, 12)]

    def behaves(tz):
        return all(tz.utcoffset(p) == zone.utcoffset(p) for p in probes)

    # The zone's winter offset says roughly where it is east to west (15 degrees per hour); among cities whose
    # clocks behave like yours, pick one near that longitude and at a latitude where most people live.
    centre = zone.utcoffset(probes[0]).total_seconds() / 3600 * 15
    best, best_score = None, None
    for city in geocoder.all_locations(geocoder.database()):
        try:
            tz = ZoneInfo(city.timezone)
        except Exception:
            continue
        if city.timezone == str(zone) or behaves(tz):
            score = abs(city.longitude - centre) + 0.5 * abs(abs(city.latitude) - 40)
            if best_score is None or score < best_score:
                best, best_score = city, score
    return (best.observer, zone) if best else (None, None)


def phase(now=None, settings=None):
    """'night', 'dawn', 'day' or 'dusk' at this moment."""
    now = now or datetime.datetime.now()
    loc = (settings or {}).get("location") or {}
    observer, zone = _place(loc.get("lat"), loc.get("lon"))
    if observer is not None:
        try:
            from astral import sun
            local = now if now.tzinfo else now.replace(tzinfo=zone)
            times = sun.sun(observer, date=local.date(), tzinfo=zone)
            sunrise, sunset = times["sunrise"], times["sunset"]
            if abs(local - sunrise) <= TWILIGHT:
                return "dawn"
            if abs(local - sunset) <= TWILIGHT:
                return "dusk"
            return "day" if sunrise < local < sunset else "night"
        except Exception:
            pass  # polar day or night, or anything odd: fall back to the clock
    hour = now.hour
    return "night" if hour >= 21 or hour < 5 else "dawn" if hour < 7 else "dusk" if hour >= 19 else "day"
