"""Pomodoro timer state machine."""
from enum import Enum, auto
import threading
from typing import Optional, Callable

from config import PomodoroConfig


class Phase(Enum):
    IDLE = auto()
    WORK = auto()
    SHORT_BREAK = auto()
    LONG_BREAK = auto()


class PomodoroTimer:
    """State machine for pomodoro timing."""

    def __init__(self, config: Optional[PomodoroConfig] = None):
        self.config = config or PomodoroConfig()
        self.phase: Phase = Phase.IDLE
        self.remaining: int = self.config.work_minutes * 60  # seconds
        self.session_count: int = 0
        self.running: bool = False
        self._listeners: list[Callable[["PomodoroTimer"], None]] = []
        self._lock = threading.Lock()

    # ── listeners ──────────────────────────────────────────

    def add_listener(self, fn: Callable[["PomodoroTimer"], None]) -> None:
        self._listeners.append(fn)

    def _notify(self) -> None:
        for fn in self._listeners:
            try:
                fn(self)
            except Exception:
                pass

    # ── core API ───────────────────────────────────────────

    def start(self) -> None:
        """Start or resume the current phase."""
        with self._lock:
            if self.phase == Phase.IDLE:
                self.phase = Phase.WORK
                self.remaining = self.config.work_minutes * 60
            self.running = True
        self._notify()

    def pause(self) -> None:
        """Pause the countdown."""
        with self._lock:
            self.running = False
        self._notify()

    def reset(self) -> None:
        """Reset to idle state."""
        with self._lock:
            self.phase = Phase.IDLE
            self.remaining = self.config.work_minutes * 60
            self.running = False
            self.session_count = 0
        self._notify()

    def tick(self) -> None:
        """Called every second. Decrements timer and handles phase transitions."""
        with self._lock:
            if not self.running:
                return
            self.remaining -= 1
            if self.remaining > 0:
                return
            # ── Phase complete ──
            self._advance_phase()
        self._notify()

    def _advance_phase(self) -> None:
        """Transition to the next phase."""
        if self.phase == Phase.WORK:
            self.session_count += 1
            if self.session_count >= self.config.sessions_before_long_break:
                self.phase = Phase.LONG_BREAK
                self.remaining = self.config.long_break_minutes * 60
                self.session_count = 0  # reset counter for next cycle
            else:
                self.phase = Phase.SHORT_BREAK
                self.remaining = self.config.short_break_minutes * 60
            self.running = self.config.auto_start_breaks
        elif self.phase in (Phase.SHORT_BREAK, Phase.LONG_BREAK):
            self.phase = Phase.WORK
            self.remaining = self.config.work_minutes * 60
            self.running = self.config.auto_start_work
        else:
            self.phase = Phase.WORK
            self.remaining = self.config.work_minutes * 60
            self.running = True

    def skip(self) -> None:
        """Skip to next phase immediately."""
        with self._lock:
            self._advance_phase()
        self._notify()

    @property
    def total(self) -> int:
        """Total seconds for the current phase."""
        mapping = {
            Phase.WORK: self.config.work_minutes * 60,
            Phase.SHORT_BREAK: self.config.short_break_minutes * 60,
            Phase.LONG_BREAK: self.config.long_break_minutes * 60,
            Phase.IDLE: 0,
        }
        return mapping[self.phase]

    @property
    def progress(self) -> float:
        """Progress of current phase as 0.0–1.0."""
        t = self.total
        return 0.0 if t == 0 else 1.0 - (self.remaining / t)

    @property
    def minutes_seconds(self) -> tuple[int, int]:
        """(minutes, seconds) remaining."""
        return divmod(self.remaining, 60)

    def formatted_time(self) -> str:
        """'MM:SS' format."""
        m, s = self.minutes_seconds
        return f"{m:02d}:{s:02d}"
