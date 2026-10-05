"""The sun by day and the moon by night: where each is in the sky right now, for drawing them behind everything.

Worked out offline with the astral library for the same place as sunrise and sunset (daylight.py): the city
picked from your time zone, or settings["location"]. Without astral, a rough rule of thumb.

The sky is laid across all your monitors together (side by side, it goes across both) as if you're facing the
equator: in the northern hemisphere the sun and moon rise on the left (east), are highest in the middle (south)
and set on the right (west); in the southern hemisphere it's the other way round. No Qt in here, so it can be
tested.
"""
import datetime
import math

SYNODIC = 29.530588853  # days from new moon to new moon
NEW_MOON = datetime.datetime(2000, 1, 6, 18, 14, tzinfo=datetime.timezone.utc)  # a known new moon
PHASES = 8  # moon sprite frames: new, waxing crescent, first quarter, waxing gibbous, full, waning...


def age(now):
    """Days since the last new moon (0 .. 29.5)."""
    when = now if now.tzinfo else now.astimezone()
    return ((when - NEW_MOON).total_seconds() / 86400) % SYNODIC


def phase_frame(now):
    """Which of the 8 moon sprite frames: 0 new, 2 first quarter, 4 full, 6 last quarter."""
    return int(round(age(now) / SYNODIC * PHASES)) % PHASES


def _place(settings):
    from pet import daylight
    loc = (settings or {}).get("location") or {}
    return daylight._place(loc.get("lat"), loc.get("lon"))


def _local(now, zone):
    if now.tzinfo:
        return now
    return now.replace(tzinfo=zone) if zone else now.astimezone()


def position(body, now, settings=None):
    """(azimuth, elevation, latitude) of "sun" or "moon" in degrees; elevation below 0: it's down."""
    observer, zone = _place(settings)
    local = _local(now, zone)
    if observer is not None:
        try:
            utc = local.astimezone(datetime.timezone.utc)  # (astral wants UTC)
            if body == "sun":
                from astral import sun
                return sun.azimuth(observer, utc), sun.elevation(observer, utc), observer.latitude
            from astral import moon
            return moon.azimuth(observer, utc), moon.elevation(observer, utc), observer.latitude
        except Exception:
            pass
    # rules of thumb: the sun is highest at half past noon; the moon about 50 minutes later each day (at
    # midnight when it's full)
    transit = 12.5 if body == "sun" else (12 + age(now) / SYNODIC * 24) % 24
    hours = (local.hour + local.minute / 60 - transit + 12) % 24 - 12  # hours since it was highest
    elevation = 55 * math.cos(hours / 12.4 * 2 * math.pi) - 12
    return 180 + hours / 6.2 * 90, elevation, 45.0


def _across(azimuth, latitude):
    if latitude < 0:  # facing north: east on the right, north in the middle, west on the left
        return max(0.0, min(1.0, ((azimuth - 270) % 360) / 180))
    return max(0.0, min(1.0, (azimuth - 90) / 180))  # facing south: east on the left, west on the right


def placement(now, settings=None):
    """What to draw in the sky now: (body, across 0 left .. 1 right, up 0 horizon .. 1 top of its arc, frame,
    mirrored), or None if neither is up. The sun when it's up; otherwise the moon if that's up. frame: the
    moon's phase (0..7; 0 for the sun). mirrored: the southern hemisphere sees the moon's phases the other way
    round."""
    for body in ("sun", "moon"):
        azimuth, elevation, latitude = position(body, now, settings)
        if elevation <= 0:
            continue
        highest = max(20.0, min(90.0, 90 - abs(latitude) + (23.5 if body == "sun" else 28)))  # about its highest
        up = max(0.0, min(1.0, elevation / highest))
        return body, _across(azimuth, latitude), up, (0 if body == "sun" else phase_frame(now)), latitude < 0
    return None


def moonrise_after(now, settings=None):
    """When the moon next rises (a local datetime), or None if that can't be worked out (no astral)."""
    observer, zone = _place(settings)
    if observer is None:
        return None
    local = _local(now, zone)
    try:
        from astral import moon
        for days in range(3):
            day = (local + datetime.timedelta(days=days)).date()
            try:
                rise = moon.moonrise(observer, day, local.tzinfo)
            except Exception:
                continue  # no moonrise that day
            if rise is not None and rise > local:
                return rise
    except Exception:
        pass
    return None


def describe(now, settings=None):
    """A few words for the tray menu: what's in the sky now, or when the moon rises."""
    found = placement(now, settings)
    if found is not None:
        return "the sun's up" if found[0] == "sun" else "the moon's up"
    rise = moonrise_after(now, settings)
    if rise is None:
        return "nothing up right now"
    return "the moon rises at " + rise.strftime("%I:%M %p").lstrip("0")
