"""Visitors: creatures that come and go, split by kind (see each file's docstring):

    base    Visitor, speech bubbles, perches
    autumn  squirrel, jay, woolly bear, geese, frog, turkeys
    crows   crows and where they perch
    bugs    inchworm, butterfly, beetles, cicada, spider
    spring  butterflies on flowers, songbirds, baby bunnies
    winter  cardinals and chickadees at the bird feeder
    night   the owl

Import from here (from pet.visitors import Crow); new visitors go in the file they belong to, and get listed below.
"""
from .base import Bubble, GRAVITY, HeadPerch, Perch, Visitor
from .autumn import (
    Frog, Goose, Jay, Migrant, Squirrel, Turkey, TurkeyFlock, Woolly, migrating_v, turkey_flock)
from .crows import (
    CAWS, Crow, CrowParty, DEN_PERCHES, FAVOURITES, PROP_PERCHES, PUMPKIN_HEIGHT, PUMPKIN_SHAPE_HEIGHT,
    SCARECROW_ARMS, TALKING, crow_party, crow_perches, favourite, scarecrow_of)
from .bugs import Beetle, Butterfly, Cicada, Inchworm, Silk, Spider
from .spring import Bunny, Flutterby, SongBird, bunnies, flower_heads, songbirds
from .winter import WinterBird, winter_birds
from .night import Owl

__all__ = [
    "Bubble", "GRAVITY", "HeadPerch", "Perch", "Visitor", "Frog", "Goose", "Jay", "Migrant", "Squirrel", "Turkey",
    "TurkeyFlock", "Woolly", "migrating_v", "turkey_flock", "CAWS", "Crow", "CrowParty", "DEN_PERCHES",
    "FAVOURITES", "PROP_PERCHES", "PUMPKIN_HEIGHT", "PUMPKIN_SHAPE_HEIGHT", "SCARECROW_ARMS", "TALKING",
    "crow_party", "crow_perches", "favourite", "scarecrow_of", "Beetle", "Butterfly", "Cicada", "Inchworm", "Silk",
    "Spider", "Flutterby", "SongBird", "flower_heads", "songbirds", "Owl", "Bunny", "bunnies", "WinterBird",
    "winter_birds",
]
