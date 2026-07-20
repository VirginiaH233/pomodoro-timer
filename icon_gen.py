"""Generate dynamic tray icon images with Pillow."""

from PIL import Image, ImageDraw, ImageFont
import os

from config import PomodoroConfig
from pomtimer import Phase


def _find_font(size: int = 14) -> ImageFont.FreeTypeFont:
    """Find a suitable monospace font for rendering time."""
    candidates = [
        "C:/Windows/Fonts/consola.ttf",         # Consolas
        "C:/Windows/Fonts/consolab.ttf",        # Consolas Bold
        "C:/Windows/Fonts/DejaVuSansMono.ttf",
        "C:/Windows/Fonts/arial.ttf",           # fallback
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def generate_icon(
    time_text: str,
    phase: Phase,
    config: PomodoroConfig,
    size: tuple[int, int] = (32, 32),
) -> Image.Image:
    """Generate a tray icon image with centered time text.

    Args:
        time_text: 'MM:SS' formatted string
        phase: Current timer phase (determines color)
        config: App config for theme colors
        size: Icon dimensions (default 32x32 for tray)
    """
    colors = config.colors

    # Choose foreground color based on phase
    if phase == Phase.WORK:
        fg = colors["work_fg"]
    elif phase in (Phase.SHORT_BREAK, Phase.LONG_BREAK):
        fg = colors["break_fg"]
    else:
        fg = colors["idle_fg"]

    bg = colors["work_bg"]

    img = Image.new("RGBA", size, (*bg, 0))  # transparent bg
    draw = ImageDraw.Draw(img)
    size_w, size_h = size

    # Fill rounded-ish background
    draw.rounded_rectangle(
        [(1, 1), (size_w - 2, size_h - 2)],
        radius=4,
        fill=(*bg, 230),
        outline=colors["border"],
        width=1,
    )

    # Determine font size based on icon dimensions
    font_size = max(8, size_w // 3)
    font = _find_font(font_size)

    # Center text
    bbox = draw.textbbox((0, 0), time_text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (size_w - tw) // 2
    y = (size_h - th) // 2 - 1

    draw.text((x, y), time_text, fill=(*fg, 255), font=font)

    return img
