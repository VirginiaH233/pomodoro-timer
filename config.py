"""Pomodoro timer configuration."""

from dataclasses import dataclass, field
import json
import os


COLOR_PRESETS = {
    "light": {
        "bg": (242, 242, 248),        "work_fg": (220, 60, 60),
        "break_fg": (50, 160, 90),     "idle_fg": (160, 160, 170),
        "label": "☀️ Light",
    },
    "dark": {
        "bg": (22, 22, 24),            "work_fg": (255, 107, 107),
        "break_fg": (129, 199, 132),   "idle_fg": (100, 100, 110),
        "label": "🌙 Dark",
    },
    "blue": {
        "bg": (234, 240, 252),         "work_fg": (50, 90, 210),
        "break_fg": (50, 170, 150),    "idle_fg": (145, 160, 185),
        "label": "💙 Blue",
    },
    "mint": {
        "bg": (234, 250, 241),         "work_fg": (200, 75, 95),
        "break_fg": (35, 155, 115),    "idle_fg": (150, 170, 160),
        "label": "🌿 Mint",
    },
    "purple": {
        "bg": (244, 240, 252),         "work_fg": (170, 55, 150),
        "break_fg": (95, 155, 115),    "idle_fg": (170, 160, 185),
        "label": "💜 Purple",
    },
    "peach": {
        "bg": (254, 240, 236),         "work_fg": (225, 95, 65),
        "break_fg": (70, 170, 130),    "idle_fg": (190, 170, 160),
        "label": "🍑 Peach",
    },
    "slate": {
        "bg": (42, 46, 54),            "work_fg": (255, 140, 100),
        "break_fg": (120, 200, 150),   "idle_fg": (115, 120, 135),
        "label": "🪨 Slate",
    },
}


@dataclass
class PomodoroConfig:
    # Timer
    work_minutes: int = 25
    short_break_minutes: int = 5
    long_break_minutes: int = 15
    sessions_before_long_break: int = 4
    auto_start_breaks: bool = True
    auto_start_work: bool = False

    # Custom names
    custom_name_work: str = ""
    custom_name_short_break: str = ""
    custom_name_long_break: str = ""

    # Appearance
    color_preset: str = "light"
    window_opacity: float = 0.88
    window_margin: int = 16
    always_on_top: bool = True

    # Behaviour
    embed_enabled: bool = True
    language: str = "中文"

    # Sounds
    sound_work: str = "beep"
    sound_short_break: str = "beep_done"
    sound_long_break: str = "beep_done"

    # Rewards
    reward_enabled: bool = True
    reward_duration_sec: int = 3

    CONFIG_FILE: str = field(default="", init=False, repr=False)

    def __post_init__(self):
        self.CONFIG_FILE = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "pomodoro_config.json",
        )
        self._load()

    def _load(self):
        if not os.path.exists(self.CONFIG_FILE):
            return
        try:
            with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k, v in data.items():
                if hasattr(self, k):
                    setattr(self, k, v)
        except (json.JSONDecodeError, IOError):
            pass

    def save(self):
        keys = (
            "work_minutes", "short_break_minutes", "long_break_minutes",
            "sessions_before_long_break", "auto_start_breaks", "auto_start_work",
            "custom_name_work", "custom_name_short_break", "custom_name_long_break",
            "color_preset", "window_opacity", "window_margin", "always_on_top",
            "embed_enabled",
            "language",
            "reward_enabled", "reward_duration_sec",
            "sound_work", "sound_short_break", "sound_long_break",
        )
        data = {k: getattr(self, k) for k in keys}
        with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @property
    def colors(self) -> dict:
        return COLOR_PRESETS.get(self.color_preset, COLOR_PRESETS["light"])

    @property
    def is_dark_preset(self) -> bool:
        """Whether this preset uses a dark background."""
        return self.color_preset in ("dark", "slate")
