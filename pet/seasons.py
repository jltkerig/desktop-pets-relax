"""Which season it is, and what belongs to each one (northern hemisphere, by month)."""
import datetime

SEASONS = ("winter", "spring", "summer", "autumn")
_BY_MONTH = {12: "winter", 1: "winter", 2: "winter", 3: "spring", 4: "spring", 5: "spring",
             6: "summer", 7: "summer", 8: "summer", 9: "autumn", 10: "autumn", 11: "autumn"}

# Items you can put out from the toy box, and the season(s) they belong to.
ITEMS = {
    "oak": {"label": "Oak tree", "seasons": ("autumn",)},
    "pumpkins": {"label": "Pumpkin patch", "seasons": ("autumn",)},
}

# Visitors that drop by on their own, per season. Winter, spring and summer come next.
VISITORS = {
    "autumn": ("squirrel", "jay", "woolly", "migrants", "geese"),
    "winter": (),
    "spring": (),
    "summer": (),
}


def season_for(day=None):
    day = day or datetime.date.today()
    return _BY_MONTH[day.month]


def items_for(season):
    return [name for name, item in ITEMS.items() if season in item["seasons"]]
