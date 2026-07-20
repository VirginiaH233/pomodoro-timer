"""Sound playback for Pomodoro timer — uses winsound (built-in, no extra deps)."""

import os
import winsound

from config import PomodoroConfig


SOUND_CHOICES = ["none", "beep", "beep_done", "bell", "chime"]
SOUND_LABELS_EN = ["🔇 Silent", "🔔 Beep", "🔔↑ Done!", "🔔 Bell", "🎵 Chime"]
SOUND_LABELS_ZH = ["🔇 静音", "🔔 蜂鸣", "🔔↑ 完成！", "🔔 铃声", "🎵 叮咚"]


def _play_beep():
    winsound.Beep(880, 500)


def _play_beep_done():
    winsound.Beep(660, 200)
    winsound.Beep(880, 300)


def _play_bell():
    winsound.Beep(440, 400)


def _play_chime():
    winsound.Beep(523, 150)
    winsound.Beep(659, 150)
    winsound.Beep(784, 250)


def _play_file(path: str):
    if not os.path.exists(path):
        winsound.Beep(200, 500)  # error beep
        return
    try:
        winsound.PlaySound(path, winsound.SND_ASYNC)
    except Exception:
        winsound.Beep(200, 500)


def play_sound(key: str):
    """Play a sound by key: 'none','beep','beep_done','bell','chime', or custom file path."""
    key = key or "none"
    if key == "none":
        return
    if key == "beep":
        _play_beep()
    elif key == "beep_done":
        _play_beep_done()
    elif key == "bell":
        _play_bell()
    elif key == "chime":
        _play_chime()
    else:
        _play_file(key.strip())


def play_phase_sound(config: PomodoroConfig):
    """Play the configured sound for the current phase transition."""
    key = getattr(config, f"sound_{config.current_phase_name}", "beep_done")
    play_sound(key)
