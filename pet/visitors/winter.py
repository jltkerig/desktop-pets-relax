"""Winter visitors: cardinals and chickadees, who come to the bird feeder (or, without one, sit in the trees and
hop about on the ground). The foxes stalk them; they always get away."""
from .base import Perch
from .crows import crow_perches
from .spring import SongBird


class WinterBird(SongBird):
    """A cardinal or a chickadee: like a songbird (it sings, pecks, flies off when a fox dashes at it), but it
    makes for the bird feeder: a spot on its seed tray, or the ground under it, pecking up spilt seed."""

    def _choose_perch(self):
        w, rng = self.world, self.world.rng
        feeder = next((t for t in w.of("yard") if t.variant == "feeder" and t.alpha >= 1), None)
        if feeder is None:
            spots = [p for p in crow_perches(w) if getattr(p.holder, "kind", None) in ("tree", "birch")]
            return rng.choice(spots) if spots and rng.random() < 0.6 else Perch(x=rng.uniform(0.1, 0.9) * w.width)
        taken = {(id(b.perch.holder), b.perch.dx) for b in w.of("songbird") if b is not self and hasattr(b, "perch")}
        free = [(dx, dy) for dx, dy in feeder.PERCHES if (id(feeder), dx) not in taken]
        if free and rng.random() < 0.75:
            return Perch(feeder, *rng.choice(free))
        return Perch(x=feeder.x + rng.uniform(-24, 24) * w.scale)  # under it, pecking up the spilt seed


def winter_birds(world):
    """A cardinal or two and a chickadee or two, arriving one after another."""
    rng = world.rng
    kinds = ["cardinal"] * rng.randint(1, 2) + ["chickadee"] * rng.randint(1, 2)
    rng.shuffle(kinds)
    birds = [WinterBird(world, kind, delay=i * 1.4) for i, kind in enumerate(kinds)]
    taken = set()
    for bird in birds:  # one bird to a spot on the feeder: any others peck about underneath
        spot = (id(bird.perch.holder), bird.perch.dx)
        if bird.perch.high and spot in taken:
            bird.perch = Perch(x=bird.perch.holder.x + rng.uniform(-24, 24) * world.scale)
        taken.add(spot)
    return birds
