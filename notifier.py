"""Desktop notifications via pystray (balloon tips from system tray)."""

from typing import Optional

from pomtimer import Phase


def notify_phase_change(
    icon: object,
    phase: Phase,
    session_count: int = 0,
) -> None:
    """Send a tray balloon notification for a phase transition.

    Args:
        icon: The pystray.Icon instance (used for .notify())
        phase: Current phase after the transition
        session_count: Total completed work sessions
    """
    messages = {
        Phase.WORK: ("🍅 工作时间", "Focus! Time for deep work."),
        Phase.SHORT_BREAK: ("☕ 短休息", "Take a 5-minute breather."),
        Phase.LONG_BREAK: (
            "🎉 长休息",
            f"Great work! Take a well-deserved 15-minute break. "
            f"Completed {session_count} sessions this cycle.",
        ),
    }

    title, msg = messages.get(phase, ("🍅 Pomodoro", "Phase changed"))

    try:
        # pystray's notify() shows a Windows balloon tip from the tray icon
        icon.notify(msg, title)
    except Exception:
        pass  # Silent fail — notifications are non-critical
