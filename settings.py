"""Settings dialog for Pomodoro Timer — resizable window, follows overlay theme."""
import tkinter as tk
from tkinter import ttk, filedialog
from config import PomodoroConfig, COLOR_PRESETS
from lang import _
from sound import play_sound, SOUND_CHOICES, SOUND_LABELS_EN, SOUND_LABELS_ZH


def _rgb(t):
    return f"#{t[0]:02x}{t[1]:02x}{t[2]:02x}"


def _is_dark(bg_rgb):
    r, g, b = bg_rgb
    return r * 0.299 + g * 0.587 + b * 0.114 < 140


LANG_DISPLAY = {"zh": "中文", "en": "English"}
_REV_LANG = {v: k for k, v in LANG_DISPLAY.items()}


class SettingsDialog:
    """Resizable modal settings window with full i18n support."""

    def __init__(self, parent: tk.Tk, config: PomodoroConfig, on_save):
        self.config = config
        self.on_save = on_save

        self.bg_rgb = config.colors["bg"]
        self.bg_hex = _rgb(self.bg_rgb)
        self.dark = _is_dark(self.bg_rgb)
        self.fg = "#d0d0d0" if self.dark else "#333333"
        self.fg_dim = "#888888" if self.dark else "#777777"
        self.entry_bg = "#3a3a3a" if self.dark else "#f0f0f0"
        self.entry_fg = "#e0e0e0" if self.dark else "#333333"
        self.btn_bg = "#555555" if self.dark else "#e0e0e0"
        self.btn_fg = "#e0e0e0" if self.dark else "#333333"
        accent = "#5a8af4"

        self.win = tk.Toplevel(parent)
        self.language = config.language
        self.win.title(_("settings_title", self.language))
        self.win.minsize(380, 420)
        self.win.geometry("460x640")
        self.win.configure(bg=self.bg_hex)
        self.win.attributes("-topmost", True)
        self.win.transient(parent)
        self.win.grab_set()

        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        self.win.geometry(f"+{(sw-460)//2}+{(sh-640)//2}")

        # Variables
        self.work_var = tk.IntVar(value=config.work_minutes)
        self.short_var = tk.IntVar(value=config.short_break_minutes)
        self.long_var = tk.IntVar(value=config.long_break_minutes)
        self.sessions_var = tk.IntVar(value=config.sessions_before_long_break)
        self.auto_break_var = tk.BooleanVar(value=config.auto_start_breaks)
        self.auto_work_var = tk.BooleanVar(value=config.auto_start_work)
        self.embed_var = tk.BooleanVar(value=config.embed_enabled)
        self.color_var = tk.StringVar(value=config.color_preset)
        self.opacity_var = tk.DoubleVar(value=config.window_opacity)
        self.topmost_var = tk.BooleanVar(value=config.always_on_top)
        self.reward_var = tk.BooleanVar(value=config.reward_enabled)
        self.lang_var = tk.StringVar(value=config.language)

        # Sound variables
        self.sound_work_var = tk.StringVar(value=config.sound_work or "beep")
        self.sound_short_var = tk.StringVar(value=config.sound_short_break or "beep_done")
        self.sound_long_var = tk.StringVar(value=config.sound_long_break or "beep_done")

        # Custom name variables
        self.name_work_var = tk.StringVar(value=config.custom_name_work or "")
        self.name_short_var = tk.StringVar(value=config.custom_name_short_break or "")
        self.name_long_var = tk.StringVar(value=config.custom_name_long_break or "")

        self._build(accent)

    # ── helpers ─────────────────────────────────────

    def _L(self, key: str) -> str:
        return _(key, self.language)

    def _color_labels(self):
        """Return list of translated color preset labels."""
        return [_(f"color_{key}", self.language) for key in COLOR_PRESETS]

    def _sect(self, parent, key: str):
        tk.Label(parent, text=self._L(key),
                 font=("Segoe UI", 10, "bold"),
                 fg=self.fg_dim, bg=self.bg_hex, anchor="w",
        ).pack(fill="x", padx=18, pady=(16, 6))

    def _row(self, parent, label_key: str, insert_fn):
        f = tk.Frame(parent, bg=self.bg_hex)
        f.pack(fill="x", padx=18, pady=4)
        tk.Label(f, text=self._L(label_key),
                 fg=self.fg, bg=self.bg_hex,
                 font=("Segoe UI", 11), anchor="w", width=22,
        ).pack(side="left")
        insert_fn(f)

    def _chk(self, parent, label_key, var):
        chk_text = tk.StringVar(value="✓" if var.get() else "✗")
        lbl = tk.Label(parent, textvariable=chk_text,
                       font=("Segoe UI", 11), fg=self.fg, bg=self.bg_hex,
                       cursor="hand2", width=2, anchor="center")
        lbl.pack(side="left")
        lbl.bind("<Button-1>", lambda e: (
            var.set(not var.get()),
            chk_text.set("✓" if var.get() else "✗"),
        ))
        lbl_text = tk.Label(parent, text=self._L(label_key),
                            fg=self.fg, bg=self.bg_hex,
                            font=("Segoe UI", 11), cursor="hand2")
        lbl_text.pack(side="left", padx=(4, 0))

    # ── build ───────────────────────────────────────

    def _build(self, accent):
        canvas = tk.Canvas(self.win, bg=self.bg_hex, highlightthickness=0)
        scroll_frame = tk.Frame(canvas, bg=self.bg_hex)
        scroll_frame.bind("<Configure>",
                          lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw", tags="inner")
        canvas.pack(side="top", fill="both", expand=True, padx=0, pady=0)

        def _wheel(event):
            canvas.yview_scroll(-1 * (event.delta // 120), "units")
        self.win.bind_all("<MouseWheel>", _wheel)
        self.win.bind("<Destroy>", lambda e: self.win.unbind_all("<MouseWheel>"))

        # ⏱  Timer
        self._sect(scroll_frame, "sect_timer")

        self._row(scroll_frame, "lbl_work_duration",
                  lambda f: (self._spin(f, self.work_var).pack(side="left"),
                             tk.Label(f, text=self._L("lbl_min"),
                                      fg=self.fg_dim, bg=self.bg_hex,
                                      font=("Segoe UI", 10)
                             ).pack(side="left", padx=(4, 0))))

        self._row(scroll_frame, "lbl_short_break",
                  lambda f: (self._spin(f, self.short_var).pack(side="left"),
                             tk.Label(f, text=self._L("lbl_min"),
                                      fg=self.fg_dim, bg=self.bg_hex,
                                      font=("Segoe UI", 10)
                             ).pack(side="left", padx=(4, 0))))

        self._row(scroll_frame, "lbl_long_break",
                  lambda f: (self._spin(f, self.long_var).pack(side="left"),
                             tk.Label(f, text=self._L("lbl_min"),
                                      fg=self.fg_dim, bg=self.bg_hex,
                                      font=("Segoe UI", 10)
                             ).pack(side="left", padx=(4, 0))))

        self._row(scroll_frame, "lbl_long_after",
                  lambda f: (self._spin(f, self.sessions_var, 1, 20).pack(side="left"),
                             tk.Label(f, text=self._L("lbl_sessions"),
                                      fg=self.fg_dim, bg=self.bg_hex,
                                      font=("Segoe UI", 10)
                             ).pack(side="left", padx=(4, 0))))

        # 📛 Custom Names
        self._sect(scroll_frame, "sect_names")
        self._row(scroll_frame, "lbl_custom_work",
                  lambda f: tk.Entry(f, textvariable=self.name_work_var,
                                    font=("Segoe UI", 11),
                                    bg=self.entry_bg, fg=self.entry_fg,
                                    relief="flat", width=16,
                                    insertbackground=self.fg,
                    ).pack(side="left"))
        self._row(scroll_frame, "lbl_custom_short",
                  lambda f: tk.Entry(f, textvariable=self.name_short_var,
                                    font=("Segoe UI", 11),
                                    bg=self.entry_bg, fg=self.entry_fg,
                                    relief="flat", width=16,
                                    insertbackground=self.fg,
                    ).pack(side="left"))
        self._row(scroll_frame, "lbl_custom_long",
                  lambda f: tk.Entry(f, textvariable=self.name_long_var,
                                    font=("Segoe UI", 11),
                                    bg=self.entry_bg, fg=self.entry_fg,
                                    relief="flat", width=16,
                                    insertbackground=self.fg,
                    ).pack(side="left"))

        # ⚙ Behavior
        self._sect(scroll_frame, "sect_behavior")
        self._row(scroll_frame, "", lambda f: self._chk(f, "lbl_auto_break", self.auto_break_var))
        self._row(scroll_frame, "", lambda f: self._chk(f, "lbl_auto_work", self.auto_work_var))
        self._row(scroll_frame, "", lambda f: self._chk(f, "lbl_snap", self.embed_var))

        # 🎨 Appearance
        self._sect(scroll_frame, "sect_appearance")

        self._row(scroll_frame, "lbl_color",
                  lambda f: self._color_combo(f).pack(side="left"))

        self._row(scroll_frame, "lbl_opacity",
                  lambda f: (
                      tk.Scale(f, from_=0.35, to=1.0, resolution=0.05,
                               orient="horizontal", variable=self.opacity_var,
                               bg=self.entry_bg, fg=self.fg, troughcolor="#444",
                               length=140, showvalue=False, highlightthickness=0,
                      ).pack(side="left", padx=(0, 8)),
                      self._pct_lbl(f).pack(side="left"),
                  ))

        self._row(scroll_frame, "", lambda f: self._chk(f, "lbl_topmost", self.topmost_var))

        # 🌐 Language
        self._row(scroll_frame, "lbl_language",
                  lambda f: self._lang_combo(f).pack(side="left"))

        # 🔊 Sound
        self._sect(scroll_frame, "sect_sound")
        self._row(scroll_frame, "lbl_sound_work",
                  lambda f: self._sound_combo(f, self.sound_work_var).pack(side="left"))
        self._row(scroll_frame, "lbl_sound_short_break",
                  lambda f: self._sound_combo(f, self.sound_short_var).pack(side="left"))
        self._row(scroll_frame, "lbl_sound_long_break",
                  lambda f: self._sound_combo(f, self.sound_long_var).pack(side="left"))

        # 🎉 Rewards
        self._sect(scroll_frame, "sect_rewards")
        self._row(scroll_frame, "", lambda f: self._chk(f, "lbl_reward", self.reward_var))

        # ── Bottom buttons ──
        btn_bar = tk.Frame(self.win, bg=self.bg_hex, height=56)
        btn_bar.pack(side="bottom", fill="x")
        btn_bar.pack_propagate(False)

        tk.Button(btn_bar, text=self._L("save"), command=self._save,
                  bg=accent, fg="#fff", relief="flat",
                  font=("Segoe UI", 11, "bold"),
                  padx=28, pady=6, cursor="hand2",
                  activebackground="#6a9aff", activeforeground="#fff",
        ).pack(side="right", padx=(0, 18), pady=10)

        tk.Button(btn_bar, text=self._L("cancel"), command=self.win.destroy,
                  bg=self.btn_bg, fg=self.btn_fg, relief="flat",
                  font=("Segoe UI", 11),
                  padx=28, pady=6, cursor="hand2",
                  activebackground="#666" if self.dark else "#d0d0d0",
                  activeforeground="#fff" if self.dark else "#333",
        ).pack(side="right", padx=(0, 8), pady=10)

    def _color_combo(self, parent):
        """Combobox showing translated color names; maps display → key on select."""
        labels = self._color_labels()
        key_order = list(COLOR_PRESETS.keys())
        combo = ttk.Combobox(parent, values=labels, state="readonly",
                             width=16, font=("Segoe UI", 10))
        # Set current value from stored key
        current_idx = key_order.index(self.color_var.get())
        combo.current(current_idx)
        # On select, map display label back to stored key
        combo.bind("<<ComboboxSelected>>", lambda e: self.color_var.set(
            self._color_key_from_label(combo.get())
        ))
        return combo

    def _color_key_from_label(self, label: str) -> str:
        rev = {_(f"color_{k}", self.language): k for k in COLOR_PRESETS}
        return rev.get(label, list(COLOR_PRESETS)[0])

    def _lang_combo(self, parent):
        """Combobox showing 中文/English; maps display → zh/en on select."""
        combo = ttk.Combobox(parent, values=["中文", "English"],
                             state="readonly", width=8, font=("Segoe UI", 10))
        combo.current(0 if self.lang_var.get() == "zh" else 1)
        combo.bind("<<ComboboxSelected>>", lambda e: self.lang_var.set(
            _REV_LANG.get(combo.get(), "zh")
        ))
        return combo

    def _spin(self, parent, var, lo=1, hi=120):
        return tk.Spinbox(parent, from_=lo, to=hi,
                          textvariable=var, width=4,
                          bg=self.entry_bg, fg=self.entry_fg,
                          buttonbackground="#555", relief="flat",
                          font=("Segoe UI", 11))

    def _pct_lbl(self, parent):
        tv = tk.StringVar(value=f"{int(self.opacity_var.get() * 100)}%")
        lbl = tk.Label(parent, textvariable=tv, fg=self.fg_dim, bg=self.bg_hex,
                       font=("Segoe UI", 10))
        self.opacity_var.trace_add("write", lambda *_: tv.set(
            f"{int(self.opacity_var.get() * 100)}%"))
        return lbl

    # ── sound ───────────────────────────────────────

    def _sound_combo(self, parent, var):
        """Combobox for sound selection. Last option opens file browser."""
        labels = SOUND_LABELS_ZH if self.language == "zh" else SOUND_LABELS_EN
        choices = SOUND_CHOICES
        combo = ttk.Combobox(parent, values=labels + [_("sound_custom", self.language)],
                             state="readonly", width=16, font=("Segoe UI", 10))
        # Map current var value to index
        cur = var.get()
        idx = choices.index(cur) if cur in choices else len(choices)
        combo.current(idx)

        def _on_select(event):
            sel = combo.current()
            if sel < len(choices):
                var.set(choices[sel])
                # Preview
                play_sound(choices[sel])
            else:
                # Browse
                fp = filedialog.askopenfilename(
                    title=_("sound_custom", self.language),
                    filetypes=[("WAV files", "*.wav"), ("All files", "*.*")],
                )
                if fp:
                    var.set(fp)
                    play_sound(fp)
                    # Update combo text to show filename
                    combo.set(_("sound_custom_set", self.language))

        combo.bind("<<ComboboxSelected>>", _on_select)
        return combo

    # ── save ────────────────────────────────────────

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
        self.config.language = self.lang_var.get()
        self.config.sound_work = self.sound_work_var.get()
        self.config.sound_short_break = self.sound_short_var.get()
        self.config.sound_long_break = self.sound_long_var.get()
        self.config.custom_name_work = self.name_work_var.get().strip()
        self.config.custom_name_short_break = self.name_short_var.get().strip()
        self.config.custom_name_long_break = self.name_long_var.get().strip()
        self.config.save()
        self.on_save(self.config)
        self.win.destroy()
