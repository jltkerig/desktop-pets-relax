"""Everything that isn't a fox, split by theme (see each file's docstring):

    common    speech bubbles, letters, rocks, twigs, crumbs: small shared pieces
    trees     the oak through the seasons, the birch, leaves, acorns
    critters  animals and insects (squirrel, birds, turkeys, crows, butterflies, bugs, owl...)
    autumn    pumpkins, scarecrow, corn, hoe, apple barrel
    yard      the den, barrels and haystacks (out all year)
    winter    sled, stump, Christmas tree, woodstack
    spring    flower beds, well
    summer    slide, pool, dahlias, dandelions, cattails
    garden    tomatoes, radishes, lettuce, watermelons
    sky       glows, paw prints, rain, snow, sun and moon

Each file has a sprites() function: name -> (frames, ms per frame, loop, anchor[, extra]). The anchor is the frame
point that sits on the item's position (the trunk base, a paw on the ground...). extra: more to write into the
sprite's JSON, such as "perches" (frame points where a bird can sit). To add a sprite, draw it in the file it
belongs to and add it to that file's sprites(). The palettes (COMMON.update) all register on import, before any
sprite is drawn.
"""
from . import autumn, common, critters, garden, sky, spring, summer, trees, winter, yard

PARTS = (common, trees, critters, autumn, yard, winter, spring, summer, garden, sky)

SPRITES = {}
for _part in PARTS:
    if hasattr(_part, "sprites"):
        SPRITES.update(_part.sprites())
