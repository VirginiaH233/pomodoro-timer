"""Pomodoro Timer — glass overlay with tray icon."""
from config import PomodoroConfig
from overlay import PomodoroOverlay


def main():
    config = PomodoroConfig()
    app = PomodoroOverlay(config)
    app.run()


if __name__ == "__main__":
    main()
