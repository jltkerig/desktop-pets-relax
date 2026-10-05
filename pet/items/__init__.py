"""Everything on the desktop that isn't a fox or a visitor, split by kind (see each file's docstring):

    base    small falling and flying bits (acorns, leaves, crumbs, drops, fluff...)
    garden  pumpkins, decorating pumpkins, melons, corn, vegetable rows, cobs and fruit
    trees   the oak and the birch
    yard    props, the hat, notes, the den, climbables
    toys    dug-up icons (balls), stolen Discord messages, desktop folders
    sky     glows, fireflies, paw prints, rain, snow

Import from here (from pet.items import Pumpkin); new things go in the file they belong to, and get listed below.
"""
from .base import (
    Acorn, Crumb, Droplet, Fluff, GRAVITY, Kernel, Leaf, Mound, PumpkinBit, SnowClump, StrawBit, Twig)
from .garden import Corn, CornCob, Crop, DecoPumpkin, Melon, Produce, Pumpkin
from .trees import Birch, Tree
from .yard import Climbable, Den, Hat, Note, Prop, Zzz
from .toys import Folder, Message, Treasure
from .sky import Firefly, Glow, PawPrint, RainDrop, SnowFlake

__all__ = [
    "Acorn", "Crumb", "Droplet", "Fluff", "GRAVITY", "Kernel", "Leaf", "Mound", "PumpkinBit", "SnowClump",
    "StrawBit", "Twig", "Corn", "CornCob", "Crop", "DecoPumpkin", "Melon", "Produce", "Pumpkin", "Birch", "Tree",
    "Climbable", "Den", "Hat", "Note", "Prop", "Zzz", "Folder", "Message", "Treasure", "Firefly", "Glow",
    "PawPrint", "RainDrop", "SnowFlake",
]
