"""Which season it is, and what belongs to each one (northern hemisphere, by month)."""
import datetime

SEASONS = ("winter", "spring", "summer", "autumn")
_BY_MONTH = {12: "winter", 1: "winter", 2: "winter", 3: "spring", 4: "spring", 5: "spring",
             6: "summer", 7: "summer", 8: "summer", 9: "autumn", 10: "autumn", 11: "autumn"}

# Items you can put out from the toy box, and the season(s) they belong to.
ITEMS = {
    "oak": {"label": "Oak tree", "seasons": ("winter", "spring", "summer", "autumn")},
    "pumpkins": {"label": "Pumpkin patch", "seasons": ("autumn",)},
    "scarecrow": {"label": "Scarecrow", "seasons": ("autumn",)},
    "corn": {"label": "Corn field", "seasons": ("autumn",)},
    "hoe": {"label": "Garden hoe", "seasons": ("autumn",)},
    "den": {"label": "Fox den", "seasons": ("winter", "spring", "summer", "autumn")},
    "barrels": {"label": "Oak barrels", "seasons": ("winter", "spring", "summer", "autumn")},
    "haystack": {"label": "Haystack", "seasons": ("summer", "autumn")},
    "sled": {"label": "Sled", "seasons": ("winter",)},
    "stump": {"label": "Tree stump", "seasons": ("winter", "spring", "summer", "autumn")},
    "xmas_tree": {"label": "Christmas tree", "seasons": ("winter",)},
    "daffodils": {"label": "Daffodils", "seasons": ("spring",)},
    "tulips": {"label": "Tulips", "seasons": ("spring",)},
    "violets": {"label": "Violets", "seasons": ("spring",)},
    "birch": {"label": "Birch tree", "seasons": ("winter", "spring", "summer", "autumn")},
    "woodstack": {"label": "Woodstack", "seasons": ("winter",)},
    "apple_barrel": {"label": "Apple barrel", "seasons": ("autumn",)},
    "well": {"label": "Stone well", "seasons": ("spring",)},
    "radishes": {"label": "Radishes", "seasons": ("spring",)},
    "lettuce": {"label": "Lettuce", "seasons": ("spring",)},
    "slide": {"label": "Slide", "seasons": ("summer",)},
    "pool": {"label": "Kiddie pool", "seasons": ("summer",)},
    "watermelons": {"label": "Watermelon patch", "seasons": ("summer",)},
    "tomatoes": {"label": "Tomato plants", "seasons": ("summer",)},
    "dahlias": {"label": "Dahlias", "seasons": ("summer", "autumn")},
    "dandelions": {"label": "Dandelions", "seasons": ("spring", "summer")},
    "cattails": {"label": "Cattails", "seasons": ("summer",)},
    "snowman": {"label": "Snowman", "seasons": ("winter",)},
    "snowballs": {"label": "Snowball pile", "seasons": ("winter",)},
    "pond": {"label": "Frozen pond", "seasons": ("winter",)},
    "feeder": {"label": "Bird feeder", "seasons": ("winter",)},
    "gifts": {"label": "Presents", "seasons": ("winter",)},
    "nest": {"label": "Robin's nest (in the oak)", "seasons": ("spring",)},
    "kite": {"label": "Kite", "seasons": ("spring",)},
    "watering_can": {"label": "Watering can", "seasons": ("spring", "summer")},
    "sprinkler": {"label": "Sprinkler", "seasons": ("summer",)},
    "beachball": {"label": "Beach ball", "seasons": ("summer",)},
    "hammock": {"label": "Hammock", "seasons": ("summer",)},
    "firefly_jar": {"label": "Firefly jar", "seasons": ("summer",)},
    "sunflowers": {"label": "Sunflowers", "seasons": ("summer",)},
}

# Visitors that drop by on their own, per season. Crows are about all year round.
VISITORS = {
    "autumn": ("squirrel", "jay", "woolly", "migrants", "geese", "turkeys", "crows", "cicada"),
    "winter": ("crows", "winterbirds"),
    "spring": ("crows", "butterflies", "songbirds", "bunnies"),
    "summer": ("crows", "junebug", "ladybug", "frog"),
}

# what each visitor is called in the tray menu's "Invite a visitor"
VISITOR_LABELS = {
    "squirrel": "Squirrel", "jay": "Blue jay", "woolly": "Woolly bear caterpillar", "migrants": "Geese flying south",
    "geese": "Geese stopping by to honk", "turkeys": "Wild turkeys", "crows": "Crows", "cicada": "Cicada",
    "winterbirds": "Cardinals and chickadees", "butterflies": "Butterflies", "songbirds": "Songbirds",
    "bunnies": "Baby bunnies", "junebug": "June beetle", "ladybug": "Ladybug", "frog": "A frog (by the water)",
    "owl": "Owl (it usually comes at night)",
}


def season_for(day=None):
    day = day or datetime.date.today()
    return _BY_MONTH[day.month]


def items_for(season):
    return [name for name, item in ITEMS.items() if season in item["seasons"]]
