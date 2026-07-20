"""Settings dialog for Pomodoro Timer."""

import tkinter as tk
from tkinter import ttk

from config import PomodoroConfig, COLOR_PRESETS


class SettingsDialog:
    """Modal settings window."""

    def __init__(self, parent: tk.Tk, config: PomodoroConfig, on_save):
        self.config = config
        self.on_save = on_save

        self.win = tk.Toplevel(parent)
        self.win.title("🍅 Pomodoro Settings")
        self.win.geometry("400x560")
        self.win.resizable(False, False)
        self.win.configure(bg="#1e1e1e")
        self.win.attributes("-topmost", True)
        self.win.transient(parent)
        self.win.grab_set()

        self._build()

    # ── helpers ──────────────────────────────────────

    def _sect(self, text: str):
        tk.Label(self.win, text=text, font=("Segoe UI", 9, "bold"),
                 fg="#888", bg="#1e1e1e", anchor="w",
        ).pack(fill="x", padx=18, pady=(14, 4))

    def _row(self, label_text: str, insert_fn, desc_text: str = ""):
        f = tk.Frame(self.win, bg="#1e1e1e")
        f.pack(fill="x", padx=18, pady=3)
        tk.Label(f, text=label_text, fg="#bbb", bg="#1e1e1e",
                 font=("Segoe UI", 10), anchor="w", width=24,
        ).pack(side="left")
        insert_fn(f)
        if desc_text:
            tk.Label(f, text=desc_text, fg="#666", bg="#1e1e1e",
                     font=("Segoe UI", 8),
            ).pack(side="left", padx=(6, 0))

    def _spin(self, var, lo=1, hi=120, parent_hint=None):
        """Create Spinbox — will be packed into its real parent."""
        sb = tk.Spinbox(parent_hint or self.win, from_=lo, to=hi,
                        textvariable=var, width=4,
                        bg="#2d2d2d", fg="#e0e0e0",
                        buttonbackground="#444", relief="flat",
                        font=("Segoe UI", 10))
        return sb

    def _pct_label(self, var, parent):
        """Create a label that shows 0–100% from a 0.0–1.0 DoubleVar."""
        tv = tk.StringVar(value=f"{int(var.get() * 100)}%")
        lbl = tk.Label(parent, textvariable=tv, fg="#888", bg="#1e1e1e",
                       font=("Segoe UI", 9))
        var.trace_add("write", lambda *_: tv.set(f"{int(var.get() * 100)}%"))
        return lbl

    # ── build ────────────────────────────────────────

    def _build(self):
        # Style
        st = ttk.Style()
        st.theme_use("clam")
        for w in ("TFrame", "TLabel"):
            st.configure(w, background="#1e1e1e", foreground="#ccc")
        st.configure("TCheckbutton", background="#1e1e1e", foreground="#ccc")
        st.map("TCheckbutton",
               background=[("active", "#1e1e1e")],
               foreground=[("active", "#fff")])

        # ── Variables ──
        self.work_var = tk.IntVar(value=self.config.work_minutes)
        self.short_var = tk.IntVar(value=self.config.short_break_minutes)
        self.long_var = tk.IntVar(value=self.config.long_break_minutes)
        self.sessions_var = tk.IntVar(value=self.config.sessions_before_long_break)
        self.auto_break_var = tk.BooleanVar(value=self.config.auto_start_breaks)
        self.auto_work_var = tk.BooleanVar(value=self.config.auto_start_work)
        self.embed_var = tk.BooleanVar(value=self.config.embed_enabled)
        self.color_var = tk.StringVar(value=self.config.color_preset)
        self.opacity_var = tk.DoubleVar(value=self.config.window_opacity)
        self.topmost_var = tk.BooleanVar(value=self.config.always_on_top)
        self.reward_var = tk.BooleanVar(value=self.config.reward_enabled)

        # ── ⏱ Timer ──
        self._sect("⏱  TIMER DURATIONS")

        self._row("Work duration",
                  lambda f: (self._spin(self.work_var).pack(in_=f, side="left"),
                             tk.Label(f, text="min", fg="#666", bg="#1e1e1e",
                                      font=("Segoe UI", 9)
                             ).pack(in_=f, side="left", padx=(4, 0))))

        self._row("Short break",
                  lambda f: (self._spin(self.short_var).pack(in_=f, side="left"),
                             tk.Label(f, text="min", fg="#666", bg="#1e1e1e",
                                      font=("Segoe UI", 9)
                             ).pack(in_=f, side="left", padx=(4, 0))))

        self._row("Long break",
                  lambda f: (self._spin(self.long_var).pack(in_=f, side="left"),
                             tk.Label(f, text="min", fg="#666", bg="#1e1e1e",
                                      font=("Segoe UI", 9)
                             ).pack(in_=f, side="left", padx=(4, 0))))

        self._row("Long break after",
                  lambda f: (self._spin(self.sessions_var, 1, 20).pack(in_=f, side="left"),
                             tk.Label(f, text="sessions", fg="#666", bg="#1e1e1e",
                                      font=("Segoe UI", 9)
                             ).pack(in_=f, side="left", padx=(4, 0))))

        # ── ⚙ Behavior ──
        self._sect("⚙  BEHAVIOR")

        self._row("", lambda f: ttk.Checkbutton(
            f, text="Auto-start breaks after work",
            variable=self.auto_break_var, style="TCheckbutton",
        ).pack(side="left"))

        self._row("", lambda f: ttk.Checkbutton(
            f, text="Auto-start work after breaks",
            variable=self.auto_work_var, style="TCheckbutton",
        ).pack(side="left"))

        self._row("", lambda f: ttk.Checkbutton(
            f, text="Snap to taskbar edge on drop",
            variable=self.embed_var, style="TCheckbutton",
        ).pack(side="left"))

        # ── 🎨 Appearance ──
        self._sect("🎨  APPEARANCE")

        color_names = [f"{v['label']} ({k})" for k, v in COLOR_PRESETS.items()]
        self._row("Color preset", lambda f: ttk.Combobox(
            f, textvariable=self.color_var,
            values=list(COLOR_PRESETS.keys()),
            state="readonly", width=10,
            font=("Segoe UI", 10),
        ).pack(side="left"))

        self._row("Transparency", lambda f: (
            tk.Scale(f, from_=0.35, to=1.0, resolution=0.05,
                     orient="horizontal", variable=self.opacity_var,
                     bg="#2d2d2d", fg="#e0e0e0", troughcolor="#444",
                     length=130, showvalue=False, highlightthickness=0,
            ).pack(side="left", padx=(0, 6)),
            self._pct_label(self.opacity_var, f).pack(side="left"),
        ))

        self._row("", lambda f: ttk.Checkbutton(
            f, text="Always on top",
            variable=self.topmost_var, style="TCheckbutton",
        ).pack(side="left"))

        # ── 🎉 Rewards ──
        self._sect("🎉  REWARDS")

        self._row("", lambda f: ttk.Checkbutton(
            f, text="Show celebration on work complete",
            variable=self.reward_var, style="TCheckbutton",
        ).pack(side="left"))

        # ── Buttons ──
        btn_frame = tk.Frame(self.win, bg="#1e1e1e")
        btn_frame.pack(fill="x", padx=18, pady=(22, 14))

        tk.Button(btn_frame, text="💾  Save", command=self._save,
                  bg="#4a8af4", fg="#fff", relief="flat",
                  font=("Segoe UI", 10, "bold"),
                  padx=24, pady=5, cursor="hand2",
                  activebackground="#5a9aff", activeforeground="#fff",
        ).pack(side="left", padx=(0, 10))

        tk.Button(btn_frame, text="Cancel", command=self.win.destroy,
                  bg="#333", fg="#aaa", relief="flat",
                  font=("Segoe UI", 10),
                  padx=24, pady=5, cursor="hand2",
                  activebackground="#444", activeforeground="#ddd",
        ).pack(side="left")

    # ── save ─────────────────────────────────────────

    def _save(self):
        self.config.work_minutes = self.work_var.get()
        self.config.short_break_minutes = self.short_var.get()
        self.config.long_break_minutes = self.long_var.get()
        self.config.sessions_before_long_break = self.sessions_var.get()
        self.config.auto_start_breaks = self.auto_break_var.get()
        self.config.auto_start_work = self.auto_work_var.get()
        self.config.embed_enabled = self.embed_var.get()
        self.config.color_preset = self.color_var.get()
        self.config.window_opacity = self.opacity_var.get()
        self.config.always_on_top = self.topmost_var.get()
        self.config.reward_enabled = self.reward_var.get()
        self.config.save()
        self.on_save(self.config)
        self.win.destroy()
