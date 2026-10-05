"""The world: everything on the desktop and how it all behaves, without any Qt, so it can be tested.

World is put together from topic files (each a class of World's methods, about one subject):

    core      what's out (rebuild), season and snow, adding and finding things, the update every frame
    garden    pumpkin and watermelon patches, decorating pumpkins, corn, vegetable rows, the hoe
    visits    who turns up, and when (leaves, acorns, visitors by season, the owl at night)
    foxplay   a fox on its own: naps, chasing leaves, pouncing, the pool, nibbling, climbing, fetching
    friends   two foxes together
    mischief  taskbar treasure, Discord messages, desktop folders
    outdoors  wind, rain and snow, night lights, fireflies, paw prints

A method lives in the file for its subject; they all share self (the World), so they can call each other.
"""
from .core import LEAF_COLOURS, Core
from .foxplay import FoxPlay
from .friends import Friends
from .garden import Garden
from .mischief import Mischief
from .outdoors import Outdoors
from .visits import Visits


class World(Core, Garden, Visits, FoxPlay, Friends, Mischief, Outdoors):
    """Everything on the desktop. See the topic files for what it does."""

__all__ = ["World", "LEAF_COLOURS"]
