"""Tray icon images for each state."""

from PIL import Image, ImageDraw

_COLORS = {
    "green": (46, 204, 113),
    "grey": (149, 165, 166),
    "orange": (230, 126, 34),
}


def make_icon(color: str) -> Image.Image:
    """Return a 64x64 filled-circle icon for the given state color."""
    rgb = _COLORS[color]
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((8, 8, 56, 56), fill=rgb)
    return img
