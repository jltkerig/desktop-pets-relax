"""The world: everything on the desktop and how it all behaves, without any Qt, so it can be tested.

World is put together from topic files (each a class of World's methods, about one subject):

    core      what's out (rebuild), season and snow, adding and finding things, the update every frame
    garden    pumpkin and watermelon patches, decorating pumpkins, corn, vegetable rows, the hoe
    visits    who turns up, and when (leaves, acorns, visitors by season, the owl at night)
    foxplay   a fox on its own: naps, chasing leaves, pouncing, the pool, nibbling, climbing, fetching
    friends   two foxes together
    mischief  taskbar treasure, Discord messages, desktop folders
    outdoors  wind, rain and snow, night lights, fireflies, paw prints
    yardfun   the newer seasonal things: putting them out, puddles, the kite, toys thrown, fox choices
    fun_winter / fun_spring / fun_summer   the games foxes play with them (snowman, pond, puddles, hammock...)

A method lives in the file for its subject; they all share self (the World), so they can call each other.
"""
from .core import LEAF_COLOURS, Core
from .foxplay import FoxPlay
from .friends import Friends
from .fun_spring import SpringFun
from .fun_summer import SummerFun
from .fun_winter import WinterFun
from .garden import Garden
from .mischief import Mischief
from .outdoors import Outdoors
from .visits import Visits
from .yardfun import YardFun


class World(Core, Garden, Visits, FoxPlay, Friends, Mischief, Outdoors, YardFun, WinterFun, SpringFun, SummerFun):
    """Everything on the desktop. See the topic files for what it does."""

__all__ = ["World", "LEAF_COLOURS"]
