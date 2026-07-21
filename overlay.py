"""Glass overlay with tray icon — Pomodoro timer UI."""

import threading
import tkinter as tk
import ctypes
from ctypes import wintypes
import win32api

import win32gui
import win32con

import pystray
from PIL import Image, ImageDraw

from pomtimer import PomodoroTimer, Phase
from config import PomodoroConfig, COLOR_PRESETS
from settings import SettingsDialog
from lang import _
from sound import play_sound


# ── Windows effects ─────────────────────────────────


def _set_rounded_corners(hwnd: int, w: int, h: int, radius: int = 10):
    """Apply rounded corners via Win32 region clipping.
    Must be called AFTER bg color is set but with NO -alpha active."""
    try:
        rgn = win32gui.CreateRoundRectRgn(0, 0, w, h, radius, radius)
        win32gui.SetWindowRgn(hwnd, rgn, True)
    except Exception:
        pass


def _set_window_alpha(hwnd: int, opacity: float):
    """Apply per-window alpha via SetLayeredWindowAttributes.
    Call AFTER SetWindowRgn to avoid corner artifacts."""
    try:
        GWL_EXSTYLE = -20
        WS_EX_LAYERED = 0x80000
        LWA_ALPHA = 0x02
        style = win32gui.GetWindowLong(hwnd, GWL_EXSTYLE)
        win32gui.SetWindowLong(hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED)
        alpha = max(0, min(255, int(opacity * 255)))
        ctypes.windll.user32.SetLayeredWindowAttributes(
            hwnd, 0, alpha, LWA_ALPHA
        )
    except Exception:
        pass


def _force_topmost(hwnd: int):
    """Check if window is covered, then re-enter topmost only if needed."""
    try:
        user32 = ctypes.windll.user32
        # Get the window directly above us in z-order
        GW_HWNDPREV = 3
        above = user32.GetWindow(hwnd, GW_HWNDPREV)
        if above == 0:
            return  # Already on top — nothing to do
        # Covered! Remove + re-enter topmost to push back on top
        HWND_NOTOPMOST = ctypes.c_int(-2)
        HWND_TOPMOST = -1
        NOMOVE_NOSIZE = 0x0002 | 0x0001
        NOACTIVATE = 0x0010
        user32.SetWindowPos(hwnd, HWND_NOTOPMOST,
                           0, 0, 0, 0, NOMOVE_NOSIZE | NOACTIVATE)
        user32.SetWindowPos(hwnd, HWND_TOPMOST,
                           0, 0, 0, 0, NOMOVE_NOSIZE)
    except Exception:
        pass


# ── Taskbar detection via Win32 API ─────────────────


ABM_GETTASKBARPOS = 0x0005
ABE_LEFT, ABE_TOP, ABE_RIGHT, ABE_BOTTOM = 0, 1, 2, 3


class APPBARDATA(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uCallbackMessage", wintypes.UINT),
        ("uEdge", wintypes.UINT),
        ("rc", wintypes.RECT),
        ("lParam", ctypes.c_long),
    ]


def get_taskbar_info():
    """Returns ((left, top, right, bottom), edge)."""
    shell32 = ctypes.windll.shell32
    abd = APPBARDATA()
    abd.cbSize = ctypes.sizeof(APPBARDATA)
    shell32.SHAppBarMessage(ABM_GETTASKBARPOS, ctypes.byref(abd))
    r = abd.rc
    return (r.left, r.top, r.right, r.bottom), abd.uEdge


# ── tray icon ───────────────────────────────────────


def _make_tray_icon() -> Image.Image:
    size = 32
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy, r = size // 2, size // 2, size // 2 - 2
    d.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=(255, 107, 107, 255))
    d.polygon([(cx - 2, cy - r), (cx + 2, cy - r), (cx, cy - r - 5)],
              fill=(129, 199, 132, 255))
    return img


# ── constants ───────────────────────────────────────

GOLD = "#FFD700"
WHITE = "#FFFFFF"
DRAG_THRESHOLD = 5    # px movement before it's considered a drag
HANDLE_SIZE = 16      # resize handle corner size
SNAP_DISTANCE = 20   # px from screen edge to trigger snap
UNSNAP_DISTANCE = 40  # px from snap anchor to trigger unsnap
ANIMATE_MS = 50       # ms per animation step
TASKBAR_GAP = 3       # px gap when window top aligns with taskbar top
EMBED_H = 28          # height in embed mode
EMBED_NEAR_DIST = 40  # px from taskbar edge to trigger embed

PHASE_EMOJI = {
    Phase.IDLE: "🍅", Phase.WORK: "⏱",
    Phase.SHORT_BREAK: "☕", Phase.LONG_BREAK: "🎉",
}


# ── corner detection helper ─────────────────────────


def _get_corner(mx: int, my: int, w: int, h: int, s: int) -> str | None:
    """Return 'tl','tr','bl','br' if mx,my is in a corner, else None."""
    top = my < s
    bot = my >= h - s
    left = mx < s
    right = mx >= w - s
    if top and left:
        return "tl"
    if top and right:
        return "tr"
    if bot and left:
        return "bl"
    if bot and right:
        return "br"
    return None


# ── overlay class ───────────────────────────────────


class PomodoroOverlay:

    MIN_W, MIN_H = 180, 34
    MAX_W, MAX_H = 500, 100
    DEF_W, DEF_H = 270, 44

    def __init__(self, config: PomodoroConfig):
        self.config = config
        self.timer = PomodoroTimer(config)
        self._notify_key = ""
        self._rewarding = False

        # Drag state
        self._drag_x = 0
        self._drag_y = 0
        self._moved = False
        self._resizing = False
        self._rs_start_w = 0
        self._rs_start_h = 0
        self._rs_start_root_x = 0
        self._rs_start_root_y = 0
        self._rs_start_win_x = 0   # window position when resize started
        self._rs_start_win_y = 0
        self._resize_corner = None  # which corner: 'tl','tr','bl','br'

        # Snap state
        self._snapped_edge: str | None = None
        self._snap_anchor_x: int = 0
        self._snap_anchor_y: int = 0

        # Embed state
        self._embed_mode = False
        self._embed_edge: int | None = None

        # Current window size
        self._win_w = self.DEF_W
        self._win_h = self.DEF_H

        # ── root window ──
        self.root = tk.Tk()
        self.root.title("Pomi")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", config.always_on_top)
        # NOTE: -alpha NOT set here; applied via _set_window_alpha AFTER
        # rounded corners to avoid black corner artifacts.

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = sw - self._win_w - config.window_margin
        y = sh - self._win_h - config.window_margin - 52
        self.root.geometry(f"{self._win_w}x{self._win_h}+{x}+{y}")

        # Set bg, apply rounded corners, THEN set alpha (order matters!)
        self.root.configure(bg="#010101")  # temp bg; will be overwritten
        self.root.update_idletasks()
        hwnd = self._hwnd()
        _set_rounded_corners(hwnd, self._win_w, self._win_h, 12)
        _set_window_alpha(hwnd, config.window_opacity)
        if config.always_on_top:
            _force_topmost(hwnd)

        # Mouse events at root level only
        self.root.bind("<Button-1>", self._on_press)
        self.root.bind("<B1-Motion>", self._on_drag)
        self.root.bind("<ButtonRelease-1>", self._on_release)
        self.root.bind("<Motion>", self._on_motion)
        self.root.bind("<Button-3>", self._show_menu)

        self._build_ui()
        self._setup_tray()
        self._refresh_all_colors()
        self.timer.add_listener(self._on_timer_event)
        self._schedule_tick()

    # ── helpers ──────────────────────────────────────

    def _hwnd(self):
        raw = self.root.winfo_id()
        return int(raw) if isinstance(raw, str) else raw

    def _refresh_window_shape(self, radius=12):
        """Re-apply rounded corners + alpha after geometry change."""
        try:
            hwnd = self._hwnd()
            _set_rounded_corners(hwnd, self._win_w, self._win_h, radius)
        except Exception:
            pass

    def _rgb(self, t) -> str:
        return f"#{t[0]:02x}{t[1]:02x}{t[2]:02x}"

    def _colors(self):
        return self.config.colors

    def _bg_hex(self):
        return self._rgb(self._colors()["bg"])

    def _fg_dim(self):
        return "#aaaaaa" if self.config.is_dark_preset else "#4a4a4a"

    def _fg_normal(self):
        return "#cccccc" if self.config.is_dark_preset else "#333333"

    def _phase_name(self) -> str:
        """Return custom name if set, else default translated phase name."""
        L = self.config.language
        p = self.timer.phase
        if p == Phase.WORK:
            return self.config.custom_name_work or _(f"phase_{p.name.lower()}", L)
        if p == Phase.SHORT_BREAK:
            return self.config.custom_name_short_break or _(f"phase_{p.name.lower()}", L)
        if p == Phase.LONG_BREAK:
            return self.config.custom_name_long_break or _(f"phase_{p.name.lower()}", L)
        return _(f"phase_{p.name.lower()}", L)

    # ── build UI ─────────────────────────────────────

    def _build_ui(self):
        bg = self._bg_hex()

        self.frame = tk.Frame(self.root, bg=bg)
        self.frame.pack(fill="both", expand=True)

        left = tk.Frame(self.frame, bg=bg)
        left.pack(side="left", padx=(12, 4))
        # Use grid for precise vertical alignment
        left.grid_rowconfigure(0, weight=1)

        self.emoji_lbl = tk.Label(left, text="⏱", font=("Segoe UI", 14),
                                  fg=self._fg_normal(), bg=bg)
        self.emoji_lbl.grid(row=0, column=0, padx=(0, 3), sticky="n")

        # Play/Pause control button — only clickable toggle
        self.ctrl_lbl = tk.Label(left, text="▶", font=("Segoe UI", 11),
                                 fg=self._fg_normal(), bg=bg,
                                 cursor="hand2")
        self.ctrl_lbl.grid(row=0, column=1, padx=(0, 4), pady=(5, 0), sticky="n")
        self.ctrl_lbl.bind("<Button-1>", lambda e: self._toggle())

        self.status_lbl = tk.Label(left, text="Pomi", font=("Segoe UI", 10),
                                   fg=self._fg_dim(), bg=bg)
        self.status_lbl.grid(row=0, column=2, pady=(5, 0), sticky="n")

        right = tk.Frame(self.frame, bg=bg)
        right.pack(side="right", padx=(0, 10))

        self.clock_lbl = tk.Label(right, text="00:00",
                                  font=("Consolas", 20, "bold"),
                                  fg=self._rgb(self._colors()["work_fg"]), bg=bg)
        self.clock_lbl.pack()

        # ── no visual resize handle; cursor changes on corners ──

    # ── embed mode ───────────────────────────────────

    def _check_and_embed(self):
        """After drag release, check if window is near taskbar → enter embed."""
        if not self.config.embed_enabled:
            return
        if self._embed_mode:
            return
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        w, h = self._win_w, self._win_h
        try:
            tb_rect, tb_edge = get_taskbar_info()
        except Exception:
            return

        tl, tt, tr, tb = tb_rect

        # Determine shortest distance from window edge to taskbar edge
        close = False
        edge = tb_edge

        if tb_edge == ABE_BOTTOM:
            # Window bottom ⇢ taskbar top
            if abs((y + h) - tt) < EMBED_NEAR_DIST:
                close = True
        elif tb_edge == ABE_TOP:
            # Window top ⇢ taskbar bottom
            if abs(y - tb) < EMBED_NEAR_DIST:
                close = True
        elif tb_edge == ABE_LEFT:
            # Window left ⇢ taskbar right
            if abs(x - tr) < EMBED_NEAR_DIST:
                close = True
        elif tb_edge == ABE_RIGHT:
            # Window right ⇢ taskbar left
            if abs((x + w) - tl) < EMBED_NEAR_DIST:
                close = True

        if close:
            self._enter_embed(edge)

    def _enter_embed(self, edge):
        """Switch to slim embed mode attached to the taskbar edge."""
        self._embed_mode = True
        self._embed_edge = edge

        # Get monitor work area
        try:
            hwnd = self._hwnd()
            monitor = win32api.MonitorFromWindow(hwnd)
            info = win32api.GetMonitorInfo(monitor)
            work = info['Work']
        except Exception:
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            work = (0, 0, sw, sh - 40)

        sw = self.root.winfo_screenwidth()
        embed_w = min(340, sw - 80)

        # Position based on taskbar edge
        if edge == ABE_BOTTOM:
            # Float just above the taskbar
            x = sw - embed_w - 30
            y = work[3] - EMBED_H  # work area bottom = above taskbar
        elif edge == ABE_TOP:
            x = sw - embed_w - 30
            y = work[1]  # work area top = below top taskbar
        elif edge == ABE_LEFT:
            x = work[0]
            y = work[3] - EMBED_H
        elif edge == ABE_RIGHT:
            x = work[2] - embed_w
            y = work[3] - EMBED_H
        else:
            return

        # Save pre-embed size for restore
        self._pre_embed_w = self._win_w
        self._pre_embed_h = self._win_h

        self._win_w = embed_w
        self._win_h = EMBED_H

        # Adjust fonts for slim mode
        self.emoji_lbl.config(font=("Segoe UI", 9))
        self.ctrl_lbl.config(font=("Segoe UI", 8))
        self.status_lbl.config(font=("Segoe UI", 7))
        self.clock_lbl.config(font=("Consolas", 13, "bold"))

        # Tighter packing — adjust internal padding
        for child in self.frame.winfo_children():
            try:
                child.pack_configure(padx=0)
            except Exception:
                pass
            for sub in child.winfo_children():
                try:
                    sub.pack_configure(padx=(0, 0))
                except Exception:
                    pass

        self.root.geometry(f"{embed_w}x{EMBED_H}+{x}+{y}")
        self.root.update_idletasks()
        self._refresh_window_shape(4)
        

    def _exit_embed(self):
        """Restore normal overlay mode."""
        if not self._embed_mode:
            return
        self._embed_mode = False
        self._embed_edge = None

        restore_w = getattr(self, '_pre_embed_w', self.DEF_W)
        restore_h = getattr(self, '_pre_embed_h', self.DEF_H)
        self._win_w = restore_w
        self._win_h = restore_h

        # Restore fonts
        self.emoji_lbl.config(font=("Segoe UI", 14))
        self.ctrl_lbl.config(font=("Segoe UI", 11))
        self.status_lbl.config(font=("Segoe UI", 10))

        # Restore packing — rebuild to be safe
        self.frame.destroy()
        self._build_ui()
        self._refresh_all_colors()

        # Clamp position
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        self.root.geometry(f"{restore_w}x{restore_h}+{x}+{y}")
        self.root.update_idletasks()
        self._refresh_window_shape(12)
        

    # ── mouse events ─────────────────────────────────

    def _on_motion(self, event):
        """Update cursor on all 4 corners for resize hints."""
        if self._embed_mode:
            self.root.config(cursor="arrow")
            return
        H = HANDLE_SIZE
        w, h = self._win_w, self._win_h
        corner = _get_corner(event.x, event.y, w, h, H)
        cursors = {
            "tl": "size_nw_se", "br": "size_nw_se",
            "tr": "size_ne_sw", "bl": "size_ne_sw",
        }
        self.root.config(cursor=cursors.get(corner, "arrow"))

    def _on_press(self, event):
        """Record drag start position. Detect resize corner."""
        self._drag_x = event.x_root
        self._drag_y = event.y_root
        self._moved = False

        if not self._embed_mode:
            H = HANDLE_SIZE
            self._resize_corner = _get_corner(event.x, event.y, self._win_w, self._win_h, H)
            if self._resize_corner:
                self._resizing = True
                self._rs_start_w = self._win_w
                self._rs_start_h = self._win_h
                self._rs_start_root_x = event.x_root
                self._rs_start_root_y = event.y_root
                self._rs_start_win_x = self.root.winfo_x()
                self._rs_start_win_y = self.root.winfo_y()
                return
        self._resizing = False
        self._resize_corner = None

    def _on_drag(self, event):
        """Drag to move or resize. Check unsnap if previously snapped.
        If in embed mode, exit embed on first significant drag."""
        dx = event.x_root - self._drag_x
        dy = event.y_root - self._drag_y

        # If in embed mode, exit on first significant drag and reposition
        if self._embed_mode and (abs(dx) > DRAG_THRESHOLD or abs(dy) > DRAG_THRESHOLD):
            self._exit_embed()
            # After exit, we need to reposition to where the drag goes
            # The existing drag continues below with updated position
            self.root.geometry(f"+{event.x_root - self._drag_x + self.root.winfo_x()}"
                               f"+{event.y_root - self._drag_y + self.root.winfo_y()}")
            self._drag_x = event.x_root
            self._drag_y = event.y_root
            return

        # Check unsnap: if snapped and dragged far enough from anchor
        if self._snapped_edge and (
                abs(event.x_root - self._snap_anchor_x) > UNSNAP_DISTANCE or
                abs(event.y_root - self._snap_anchor_y) > UNSNAP_DISTANCE):
            self._snapped_edge = None

        if self._resizing:
            corner = self._resize_corner
            dx = event.x_root - self._rs_start_root_x
            dy = event.y_root - self._rs_start_root_y

            new_w = self._rs_start_w
            new_h = self._rs_start_h
            new_x = self._rs_start_win_x
            new_y = self._rs_start_win_y

            if corner == "br":
                new_w += dx
                new_h += dy
            elif corner == "bl":
                new_w -= dx
                new_h += dy
                new_x += dx
            elif corner == "tr":
                new_w += dx
                new_h -= dy
                new_y += dy
            elif corner == "tl":
                new_w -= dx
                new_h -= dy
                new_x += dx
                new_y += dy

            new_w = max(self.MIN_W, min(self.MAX_W, new_w))
            new_h = max(self.MIN_H, min(self.MAX_H, new_h))
            self._win_w = new_w
            self._win_h = new_h
            self.root.geometry(f"{new_w}x{new_h}+{new_x}+{new_y}")
            self.root.update_idletasks()
            self._refresh_window_shape(12)
            self._moved = True
        elif abs(dx) > DRAG_THRESHOLD or abs(dy) > DRAG_THRESHOLD:
            # Move mode
            self._moved = True
            x = self.root.winfo_x() + dx
            y = self.root.winfo_y() + dy
            self.root.geometry(f"+{x}+{y}")
            self._drag_x = event.x_root
            self._drag_y = event.y_root

    def _on_release(self, event):
        """If not a drag, do nothing — only ctrl_lbl toggles.
        After drag, check for embed mode."""
        if self._resizing:
            self._resizing = False
            self._resize_corner = None
            return
        if not self._moved:
            # ignore click — only ctrl_lbl toggles
            return
        self._moved = False

        # Check for magnetic snap to screen edge
        self._snap_to_edge()
        # Check if window was dragged near taskbar → enter embed mode
        self._check_and_embed()

    # ── control button toggle ─────────────────────────

    def _toggle(self):
        """Play/Pause toggle — only called from ctrl_lbl click."""
        if self.timer.running:
            self.timer.pause()
        elif self.timer.phase == Phase.IDLE:
            self.timer.start()
        else:
            self.timer.start()

    # ── magnetic snapping ────────────────────────────

    def _snap_to_edge(self):
        """After a drag, check proximity to monitor edges and snap if close."""
        if self._embed_mode:
            return
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        w, h = self._win_w, self._win_h

        # Get current monitor's work area (excludes taskbar)
        try:
            hwnd = self._hwnd()
            monitor = win32api.MonitorFromWindow(hwnd)
            info = win32api.GetMonitorInfo(monitor)
            wa = info['Work']  # (left, top, right, bottom)
            ma = info['Monitor']  # full monitor rect
            work_l, work_t, work_r, work_b = wa
            # Determine taskbar edge by comparing monitor vs work area
            tb_on_bottom = work_b < ma[3]
            tb_on_top = work_t > ma[1]
            tb_on_left = work_l > ma[0]
            tb_on_right = work_r < ma[2]
        except Exception:
            # Fallback to screen dimensions
            work_l = 0
            work_t = 0
            work_r = self.root.winfo_screenwidth()
            work_b = self.root.winfo_screenheight()
            tb_on_bottom = tb_on_top = tb_on_left = tb_on_right = False

        snap_x = None
        snap_y = None
        edge = []

        # Snap to work area edges (these already account for taskbar)
        # Left edge
        if x < (work_l + SNAP_DISTANCE):
            snap_x = work_l
            edge.append("left")
        # Right edge
        if (x + w) > (work_r - SNAP_DISTANCE):
            snap_x = work_r - w
            edge.append("right")
        # Top edge
        if y < (work_t + SNAP_DISTANCE):
            snap_y = work_t
            edge.append("top")
        # Bottom edge (taskbar top area): three behaviors
        # 1. Dragged past monitor bottom → recover: snap top near taskbar top (with gap)
        # 2. Window bottom closer to taskbar top → snap above (flush)
        # 3. Window top closer to taskbar top → snap top near taskbar top (with gap, like embedded)
        at_screen_bottom = tb_on_bottom and (y + h) >= ma[3]  # fully past work area
        if at_screen_bottom:
            snap_y = work_b + TASKBAR_GAP
            edge.append("bottom_gap")
        else:
            bot_dist = abs((y + h) - work_b)  # window bottom → taskbar top
            top_dist = abs(y - work_b)        # window top → taskbar top
            if bot_dist < SNAP_DISTANCE or top_dist < SNAP_DISTANCE:
                if bot_dist < top_dist:
                    snap_y = work_b - h       # bottom flush with taskbar top
                    edge.append("bottom")
                else:
                    snap_y = work_b + TASKBAR_GAP  # top near taskbar top, with gap
                    edge.append("bottom_gap")

        if snap_x is not None or snap_y is not None:
            target_x = x if snap_x is None else snap_x
            target_y = y if snap_y is None else snap_y
            self._snapped_edge = "_".join(edge) if edge else None
            self._snap_anchor_x = target_x + w // 2
            self._snap_anchor_y = target_y + h // 2
            self._animate_to(target_x, target_y)

    def _animate_to(self, target_x, target_y):
        """Smoothly animate the window to the target position."""
        cur_x = self.root.winfo_x()
        cur_y = self.root.winfo_y()
        if cur_x == target_x and cur_y == target_y:
            return
        step_x = (target_x - cur_x) // 3
        step_y = (target_y - cur_y) // 3
        if step_x == 0 and step_y == 0:
            step_x = 1 if target_x > cur_x else (-1 if target_x < cur_x else 0)
            step_y = 1 if target_y > cur_y else (-1 if target_y < cur_y else 0)
        next_x = cur_x + step_x
        next_y = cur_y + step_y
        if (step_x > 0 and next_x > target_x) or (step_x < 0 and next_x < target_x):
            next_x = target_x
        if (step_y > 0 and next_y > target_y) or (step_y < 0 and next_y < target_y):
            next_y = target_y
        self.root.geometry(f"+{next_x}+{next_y}")
        if next_x != target_x or next_y != target_y:
            self.root.after(ANIMATE_MS, lambda: self._animate_to(target_x, target_y))

    # ── right-click menu ─────────────────────────────

    def _show_menu(self, event):
        menu = tk.Menu(self.root, tearoff=0, bg="#2d2d2d", fg="#e0e0e0",
                       activebackground="#555", activeforeground="#fff")
        phase = self.timer.phase
        L = self.config.language

        emb = _("embedded", L) if self._embed_mode else ""
        phase_name = self._phase_name()
        menu.add_command(
            label=f"{self.timer.formatted_time()}  {phase_name}{emb}",
            state="disabled")
        menu.add_separator()

        if self.timer.running:
            menu.add_command(label=_("pause", L), command=self.timer.pause)
        else:
            lbl = _("start", L) if phase == Phase.IDLE else _("resume", L)
            menu.add_command(label=lbl, command=self.timer.start)
        if phase != Phase.IDLE:
            if self.timer.running:
                menu.add_command(label=_("skip", L), command=self.timer.skip)
            menu.add_command(label=_("reset", L), command=self.timer.reset)
        menu.add_separator()

        color_m = tk.Menu(menu, tearoff=0, bg="#2d2d2d", fg="#e0e0e0")
        for key in COLOR_PRESETS:
            chk = "✓ " if key == self.config.color_preset else "  "
            color_m.add_command(
                label=f"{chk} {_(f'color_{key}', L)}",
                command=lambda k=key: self._switch_color(k),
            )
        menu.add_cascade(label=f"{_('color', L)}", menu=color_m)

        if self._embed_mode:
            menu.add_command(label=_("detach", L),
                             command=self._exit_embed)
        else:
            menu.add_separator()

        menu.add_command(label=_("settings", L), command=self._open_settings)
        menu.add_command(label=_("recall", L), command=self._recall)
        menu.add_command(label=_("quit", L), command=self._on_quit)

        menu.tk_popup(event.x_root, event.y_root)

    def _switch_color(self, key):
        self.config.color_preset = key
        self.config.save()
        self._refresh_all_colors()

    # ── settings ─────────────────────────────────────

    def _open_settings(self):
        def on_save(cfg):
            self.config = cfg
            self.timer.config = cfg
            hwnd = self._hwnd()
            _set_window_alpha(hwnd, cfg.window_opacity)
            self.root.attributes("-topmost", cfg.always_on_top)
            if cfg.always_on_top:
                _force_topmost(hwnd)
            self._refresh_all_colors()
            self._rebuild_tray_menu()
        SettingsDialog(self.root, self.config, on_save)

    # ── tray ─────────────────────────────────────────

    def _setup_tray(self):
        self.tray_icon = pystray.Icon(
            "Pomi", _make_tray_icon(), _("focus", self.config.language),
            menu=self._build_tray_menu(),
        )
        t = threading.Thread(target=self.tray_icon.run, daemon=True)
        t.start()

    def _rebuild_tray_menu(self):
        if self.tray_icon:
            self.tray_icon.menu = self._build_tray_menu()

    def _build_tray_menu(self):
        phase = self.timer.phase
        L = self.config.language
        items = []
        emb = _("embedded", L) if self._embed_mode else ""
        phase_name = self._phase_name()
        items.append(pystray.MenuItem(
            f"{self.timer.formatted_time()} — {phase_name}{emb}",
            None, enabled=False))
        items.append(pystray.Menu.SEPARATOR)
        if self.timer.running:
            items.append(pystray.MenuItem(_("pause", L), self._on_pause, default=True))
        else:
            lbl = _("start", L) if phase == Phase.IDLE else _("resume", L)
            items.append(pystray.MenuItem(lbl, self._on_start, default=True))
        if phase != Phase.IDLE:
            if self.timer.running:
                items.append(pystray.MenuItem(_("skip", L), self._on_skip))
            items.append(pystray.MenuItem(_("reset", L), self._on_reset))
        items.append(pystray.Menu.SEPARATOR)
        items.append(pystray.MenuItem(_("recall", L), self._recall))
        if self._embed_mode:
            items.append(pystray.MenuItem(
                _("detach", L), self._exit_embed))
        items.append(pystray.MenuItem(_("settings", L), self._open_settings))
        items.append(pystray.Menu.SEPARATOR)
        items.append(pystray.MenuItem(_("quit", L), self._on_quit))
        return pystray.Menu(*items)

    def _on_start(self): self.timer.start()
    def _on_pause(self): self.timer.pause()
    def _on_reset(self): self.timer.reset(); self._notify_key = ""
    def _on_skip(self): self.timer.skip()

    # ── timer events ─────────────────────────────────

    def _on_timer_event(self, _timer=None):
        phase = self.timer.phase
        nk = f"{phase.name}_{self.timer.session_count}"
        if nk == self._notify_key:
            return
        self._notify_key = nk

        # Play phase-transition sound (skip IDLE → WORK which happens on manual start)
        sound_key = getattr(self.config, f"sound_{phase.name.lower()}", "beep_done")
        play_sound(sound_key)

        if phase in (Phase.SHORT_BREAK, Phase.LONG_BREAK):
            if self.config.reward_enabled:
                self._show_reward()
        self._tray_notify(phase)

    def _tray_notify(self, phase):
        L = self.config.language
        msgs = {
            Phase.SHORT_BREAK: (_("notify_short_break_title", L),
                                _("notify_short_break_msg", L)),
            Phase.LONG_BREAK: (_("notify_long_break_title", L),
                               _("notify_long_break_msg", L)),
            Phase.WORK: (_("notify_work_title", L),
                         _("notify_work_msg", L)),
        }
        title, msg = msgs.get(phase, ("Pomi", "Phase changed"))
        try:
            if self.tray_icon:
                self.tray_icon.notify(msg, title)
        except Exception:
            pass

    # ── reward ───────────────────────────────────────

    def _show_reward(self):
        if self._rewarding:
            return
        self._rewarding = True
        self._flash_reward(0)

    def _flash_reward(self, step):
        if step >= 6:
            self._rewarding = False
            self._update_display()
            return
        L = self.config.language
        if step % 2 == 0:
            self.clock_lbl.config(text=_("reward_done", L), fg=GOLD,
                                  font=("Segoe UI", 14, "bold"))
        else:
            self.clock_lbl.config(text=_("reward_great", L), fg=WHITE,
                                  font=("Segoe UI", 14, "bold"))
        self.root.after(500, lambda: self._flash_reward(step + 1))

    # ── display refresh ─────────────────────────────

    def _refresh_all_colors(self):
        bg = self._bg_hex()
        fg = self._fg_normal()
        fd = self._fg_dim()

        self.root.configure(bg=bg)

        # Check if UI is built yet
        if not hasattr(self, 'frame'):
            return

        self.frame.configure(bg=bg)

        for child in self.frame.winfo_children():
            try:
                child.configure(bg=bg)
                for sub in child.winfo_children():
                    try:
                        sub.configure(bg=bg)
                    except Exception:
                        pass
            except Exception:
                pass

        if hasattr(self, 'emoji_lbl'):
            self.emoji_lbl.configure(fg=fg)
        if hasattr(self, 'ctrl_lbl'):
            self.ctrl_lbl.configure(fg=fg)
        if hasattr(self, 'status_lbl'):
            self.status_lbl.configure(fg=fd)
        self._update_display()

    def _update_display(self):
        if self._rewarding:
            return
        c = self._colors()
        phase = self.timer.phase

        if hasattr(self, 'emoji_lbl'):
            self.emoji_lbl.config(text=PHASE_EMOJI.get(phase, "🍅"))
        if hasattr(self, 'ctrl_lbl'):
            self.ctrl_lbl.config(text="⏸" if self.timer.running else "▶")
        if hasattr(self, 'status_lbl'):
            self.status_lbl.config(text=self._phase_name())

        clock_color = self._rgb(
            c["work_fg"] if phase == Phase.WORK
            else c["break_fg"] if phase in (Phase.SHORT_BREAK, Phase.LONG_BREAK)
            else c["idle_fg"]
        )

        fs = max(14, min(20, self._win_w // 13))
        self.clock_lbl.config(
            text=self.timer.formatted_time(),
            fg=clock_color,
            font=("Consolas", fs, "bold"),
        )

    def _schedule_tick(self):
        try:
            self.timer.tick()
            self._update_display()
            self._rebuild_tray_menu()
            _force_topmost(self._hwnd())
        except Exception:
            pass
        self.root.after(1000, self._schedule_tick)

    # ── quit ─────────────────────────────────────────

    def _on_quit(self):
        try:
            self.tray_icon.stop()
        except Exception:
            pass
        self.root.quit()
        self.root.destroy()

    def _recall(self):
        """Force the overlay to show on top — for when it gets lost behind the taskbar."""
        hwnd = self._hwnd()
        self.root.deiconify()
        self.root.lift()
        _force_topmost(hwnd)
        # Also reposition to a safe area if off-screen
        try:
            x = self.root.winfo_x()
            y = self.root.winfo_y()
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            if x < -self._win_w // 2 or x > sw:
                x = sw - self._win_w - self.config.window_margin
            if y < -self._win_h // 2 or y > sh - 20:
                y = sh - self._win_h - self.config.window_margin - 52
            self.root.geometry(f"+{x}+{y}")
        except Exception:
            pass

    def run(self):
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self._on_quit()
