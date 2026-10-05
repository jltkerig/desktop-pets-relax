"""The sun and moon as a clock: the sun crosses the sky from 6 AM to 6 PM and the moon from 6 PM to 6 AM, rising on
the left, highest in the middle at noon (or midnight), setting on the right, across all the monitors together. So
you can tell roughly what time it is at a glance. The moon shows its real phase (but never quite vanishes: a new
moon shows as a thin crescent). No Qt in here, so it can be tested.
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


def placement(now, settings=None):
    """What to draw now: (body, across 0 left .. 1 right, up 0 horizon .. 1 top of its arc, frame, mirrored).
    The sun from 6 AM to 6 PM, the moon from 6 PM to 6 AM. frame: the moon's phase (0 for the sun)."""
    hours = now.hour + now.minute / 60 + now.second / 3600
    day = 6 <= hours < 18
    across = ((hours - 6) % 12) / 12  # 0 at 6 o'clock, 0.5 at noon or midnight, nearly 1 just before 6
    up = math.sin(math.pi * across)
    if day:
        return "sun", across, up, 0, False
    frame = phase_frame(now)
    if frame == 0:  # a new moon would be all but invisible: show the first sliver instead
        frame = 1 if age(now) < SYNODIC / 2 else 7
    return "moon", across, up, frame, False


def describe(now, settings=None):
    """A few words for the tray menu."""
    return "the sun 6 AM to 6 PM, the moon 6 PM to 6 AM"
