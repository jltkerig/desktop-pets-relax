"""Pictures for the Discord mischief: finding Discord's plain background colour, and lifting just the words
of a message off it."""
from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QImage


AVATAR_COLUMN = 44  # Qt pixels at the left of the chat column where avatars are (never taken)


def text_only(image, background, skip_left=0):
    """Just the text out of a picture of a Discord message: (picture with the background see-through, the part
    of the original it came from as a QRect), or None if there's no text. background: a QColor."""
    w, h = image.width(), image.height()
    br, bg_, bb = background.red(), background.green(), background.blue()

    def diff(c):
        return max(abs(c.red() - br), abs(c.green() - bg_), abs(c.blue() - bb))

    xs, ys = [], []
    for y in range(h):
        for x in range(max(0, skip_left), w):
            if diff(image.pixelColor(x, y)) > 48:
                xs.append(x)
                ys.append(y)
    if len(xs) < 12:
        return None
    left, right = max(skip_left, min(xs) - 2), min(w - 1, max(xs) + 2)
    top, bottom = max(0, min(ys) - 2), min(h - 1, max(ys) + 2)
    out = QImage(right - left + 1, bottom - top + 1, QImage.Format_ARGB32)
    out.fill(Qt.transparent)
    for y in range(top, bottom + 1):
        for x in range(left, right + 1):
            c = image.pixelColor(x, y)
            d = diff(c)
            if d >= 14:  # text (its soft edges partly see-through)
                out.setPixelColor(x - left, y - top, QColor(c.red(), c.green(), c.blue(), min(255, (d - 14) * 4)))
    # a thin dark outline round the letters, so they read on grass, sky or snow
    ow, oh = out.width(), out.height()
    solid = {(x, y) for y in range(oh) for x in range(ow) if out.pixelColor(x, y).alpha() > 120}
    edge = QColor(max(0, br - 20), max(0, bg_ - 20), max(0, bb - 20), 200)
    for x, y in solid:
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < ow and 0 <= ny < oh and (nx, ny) not in solid and out.pixelColor(nx, ny).alpha() < 120:
                out.setPixelColor(nx, ny, edge)
    return out, QRect(left, top, right - left + 1, bottom - top + 1)


def background_colour(image):
    """The plain colour all round the edge of a picture (Discord's background behind a message), or None if
    the edges aren't mostly one colour (or the picture is empty)."""
    if image.isNull() or image.width() < 8 or image.height() < 4:
        return None
    w, h = image.width(), image.height()
    edge = [(x, y) for x in range(0, w, 3) for y in (0, 1, h - 2, h - 1)] + \
           [(x, y) for y in range(0, h, 2) for x in (0, 1, 2, w - 3, w - 2, w - 1)]
    counts = {}
    for x, y in edge:
        rgb = image.pixelColor(x, y).rgb() & 0xFFFFFF
        counts[rgb] = counts.get(rgb, 0) + 1
    rgb, n = max(counts.items(), key=lambda kv: kv[1])
    if n < len(edge) * 0.6:
        return None
    if rgb == 0 and n == len(edge) and all(image.pixelColor(x, y).rgb() & 0xFFFFFF == 0
                                           for x in range(0, w, 4) for y in range(0, h, 4)):
        return None  # all black: the screen couldn't be copied
    return QColor(rgb >> 16 & 255, rgb >> 8 & 255, rgb & 255)
