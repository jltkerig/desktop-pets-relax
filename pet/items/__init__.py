"""Everything on the desktop that isn't a fox or a visitor, split by kind (see each file's docstring):

    base    small falling and flying bits (acorns, leaves, crumbs, drops, fluff...)
    garden  pumpkins, decorating pumpkins, melons, corn, vegetable rows, cobs and fruit
    trees   the oak and the birch
    yard    props, the hat, notes, the den, climbables
    toys    dug-up icons (balls), stolen Discord messages, desktop folders
    sky     glows, fireflies, paw prints, rain, snow
    play    YardThing (the newer seasonal things' base) and Ball (a toy to throw)
    winter  snowman and carrot, snowball pile and snowballs, frozen pond, bird feeder, gift boxes
    spring  puddles and muddy paw prints, the robin's nest, the kite, the watering can
    summer  sprinkler, beach ball, hammock, firefly jar, sunflowers

Import from here (from pet.items import Pumpkin); new things go in the file they belong to, and get listed below.
"""
from .base import (
    Acorn, Crumb, Droplet, Fluff, GRAVITY, Kernel, Leaf, Mound, PumpkinBit, SnowClump, StrawBit, Twig)
from .garden import Corn, CornCob, Crop, DecoPumpkin, Melon, Produce, Pumpkin
from .trees import Birch, Tree
from .yard import Climbable, Den, Hat, Note, Prop, Zzz
from .toys import Folder, Message, Treasure
from .sky import Firefly, Glow, PawPrint, RainDrop, SnowFlake
from .play import Ball, YardThing
from .winter import Carrot, Feeder, Gifts, Pond, Snowball, SnowballPile, Snowman
from .spring import Kite, MudPrint, Nest, Puddle, WateringCan
from .summer import BeachBall, FireflyJar, Hammock, HammockFront, Sprinkler, Sunflowers

__all__ = [
    "Acorn", "Crumb", "Droplet", "Fluff", "GRAVITY", "Kernel", "Leaf", "Mound", "PumpkinBit", "SnowClump",
    "StrawBit", "Twig", "Corn", "CornCob", "Crop", "DecoPumpkin", "Melon", "Produce", "Pumpkin", "Birch", "Tree",
    "Climbable", "Den", "Hat", "Note", "Prop", "Zzz", "Folder", "Message", "Treasure", "Firefly", "Glow",
    "PawPrint", "RainDrop", "SnowFlake", "Ball", "YardThing", "Carrot", "Feeder", "Gifts", "Pond", "Snowball",
    "SnowballPile", "Snowman", "Kite", "MudPrint", "Nest", "Puddle", "WateringCan", "BeachBall", "FireflyJar",
    "Hammock", "HammockFront", "Sprinkler", "Sunflowers",
]
