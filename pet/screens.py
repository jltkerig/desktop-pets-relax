"""How the monitors are laid out for the pets. No Qt here, so it can be tested.

All monitors are joined into one long strip of ground, left to right in the order Windows arranges them.
Each monitor shows its own slice of the strip, with the ground on the top edge of its taskbar (or the
bottom of the screen if that monitor has no taskbar). A fox walking off one screen's edge walks onto
the next.
"""


def layout(areas):
    """areas: the work area (x, y, width, height) of each monitor, in any order.

    Returns (slices, strip_width, strip_height): one slice per monitor, ordered left to right, each a dict
    with the monitor's area and "offset" (where its slice starts along the strip), plus the strip's size.
    Monitors stacked above each other are put one after the other too, so every screen gets its share.
    """
    ordered = sorted(areas, key=lambda a: (a[0], a[1]))
    slices, offset = [], 0
    for x, y, w, h in ordered:
        slices.append({"x": x, "y": y, "w": w, "h": h, "offset": offset})
        offset += w
    height = max((h for _, _, _, h in ordered), default=0)
    return slices, offset, height


def slice_at(slices, strip_x):
    """The monitor slice showing strip position strip_x (the nearest one past either end)."""
    if not slices:
        return None
    for s in slices:
        if s["offset"] <= strip_x < s["offset"] + s["w"]:
            return s
    return slices[0] if strip_x < 0 else slices[-1]
