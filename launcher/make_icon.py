"""Makes launcher/fox.ico from the tray icon sprite (the fox face), at the sizes Windows uses."""
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
face = Image.open(HERE.parent / "art" / "sprites" / "tray_icon.png").convert("RGBA")
big = face.resize((256, 256), Image.NEAREST)  # stays crisp pixel art
big.save(HERE / "fox.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
