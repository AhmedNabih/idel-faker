"""Tray icon images for each state, and .ico export for packaging."""

from PIL import Image, ImageDraw

_COLORS = {
    "green": (46, 204, 113),
    "grey": (149, 165, 166),
    "orange": (230, 126, 34),
}

_ICO_SIZES = [(16, 16), (32, 32), (48, 48), (64, 64), (256, 256)]


def make_icon(color: str, size: int = 64) -> Image.Image:
    """Return a filled-circle icon of `size`x`size` for the given state color."""
    rgb = _COLORS[color]
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    pad = size // 8
    draw.ellipse((pad, pad, size - pad, size - pad), fill=rgb)
    return img


def save_ico(path: str) -> None:
    """Write a multi-size Windows .ico (from the green state icon) to `path`."""
    make_icon("green", 256).save(path, format="ICO", sizes=_ICO_SIZES)
