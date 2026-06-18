import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import subprocess
import threading
import os
import sys
import shutil

CREDIT_TEXT = "Made by Noelle :3"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def resource_path(relative):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)

def find_ytdlp():
    bundled = resource_path("bin/yt-dlp.exe")
    if os.path.isfile(bundled):
        return bundled
    return shutil.which("yt-dlp") or shutil.which("yt-dlp.exe")

# ---------------------------------------------------------------------------
# Theme definitions
# ---------------------------------------------------------------------------

THEMES = {
    "light": {
        "bg":         "#F5F5F5",
        "card":       "#FFFFFF",
        "border":     "#DCDCDC",
        "fg":         "#111111",
        "fg2":        "#6B7280",
        "entry_bg":   "#FFFFFF",
        "btn_bg":     "#E8E8E8",
        "btn_fg":     "#333333",
        "folder_bg":  "#F0F0F0",
        "log_bg":     "#1E1E1E",
        "log_fg":     "#D4D4D4",
        "accent":     "#CC3300",       # fire red-orange
        "accent_hov": "#AA2200",
        "credit_fg":  "#AAAAAA",
        "header_bg":  "#EBEBEB",
        "toggle_icon":"🌙",
        "combo_field":"#FFFFFF",
        "combo_fg":   "#111111",
        "list_bg":    "#FFFFFF",
        "list_sel":   "#CC3300",
        "list_sel_fg":"#FFFFFF",
    },
    "dark": {
        "bg":         "#111111",
        "card":       "#1A1A1A",
        "border":     "#2E2E2E",
        "fg":         "#E0E0E0",
        "fg2":        "#AAAAAA",
        "entry_bg":   "#2A2A2A",
        "btn_bg":     "#2A2A2A",
        "btn_fg":     "#CCCCCC",
        "folder_bg":  "#2A2A2A",
        "log_bg":     "#0A0A0A",
        "log_fg":     "#AAAAAA",
        "accent":     "#CC3300",       # fire red-orange (same in both themes)
        "accent_hov": "#AA2200",
        "credit_fg":  "#444444",
        "header_bg":  "#0D0D0D",
        "toggle_icon":"☀️",
        "combo_field":"#2A2A2A",       # visible dark field
        "combo_fg":   "#E0E0E0",       # white text in dropdown
        "list_bg":    "#1A1A1A",
        "list_sel":   "#CC3300",
        "list_sel_fg":"#FFFFFF",
    },
}

QUALITY_OPTIONS = {
    "Video + Audio": ["Best", "1080p", "720p", "480p", "360p", "240p"],
    "Video":         ["Best", "1080p", "720p", "480p", "360p", "240p"],
    "Audio":         ["Best (auto)"],
}

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("My Awesome YouTube Downloader")
        self.resizable(False, False)
        self._theme_name = "light"
        self._process    = None
        self._download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        self._gif_frames    = []
        self._gif_durations = []
        self._gif_index     = 0
        self._after_id      = None
        self._closing       = False
        

        # per-button GIF animation state
        self._btn_gif   = {}   # key -> {"frames","durations","index","after_id","label"}

        # bulk state
        self._bulk_queue   = []
        self._bulk_index   = 0
        self._bulk_running = False

        # playlist state
        self._pl_queue   = []
        self._pl_index   = 0
        self._pl_running = False

        # music state
        self._music_proc = None

        # icon
        icon_png = resource_path("assets/icons/icon.png")
        icon_ico = resource_path("assets/icons/icon.ico")
        try:
            if os.path.isfile(icon_png):
                _big   = ImageTk.PhotoImage(Image.open(icon_png).resize((256,256), Image.LANCZOS))
                _small = ImageTk.PhotoImage(Image.open(icon_png).resize((32,32),   Image.LANCZOS))
                self.iconphoto(True, _big, _small)
                self._icon_refs = [_big, _small]
            elif os.path.isfile(icon_ico):
                self.iconbitmap(icon_ico)
        except Exception:
            pass

        self._load_images()
        self._build_ui()
        self._apply_theme()
        self._start_gif()
        self._start_music()
        self._check_ytdlp()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # Music
    # ------------------------------------------------------------------

    def _start_music(self):
        if self._closing:
            return
        mp3 = resource_path("assets/audio/theme.mp3")
        if not os.path.isfile(mp3):
            return
        # Use ffplay (bundled with ffmpeg) or vlc if available, loop forever
        player = shutil.which("ffplay") or resource_path("bin/ffplay.exe")
        if os.path.isfile(str(player)) or shutil.which("ffplay"):
            cmd = [player, "-nodisp", "-autoexit", "-loop", "0", mp3]
        else:
            vlc = shutil.which("vlc")
            if vlc:
                cmd = [vlc, "--intf", "dummy", "--repeat", mp3]
            else:
                return   # no player found

        try:
            self._music_proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            # restart when it ends (loop fallback for players that don't support -loop)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Image / GIF loading
    # ------------------------------------------------------------------

    def _load_images(self):
        # Cat – 120px tall
        cat_path = resource_path("assets/images/cat.png")
        self._cat_photo = None
        if os.path.isfile(cat_path):
            img = Image.open(cat_path).convert("RGBA")
            w, h = img.size
            nh = 120; nw = int(w * nh / h)
            self._cat_photo = ImageTk.PhotoImage(img.resize((nw, nh), Image.LANCZOS))

        # Title GIF – 60px tall
        self._gif_frames    = []
        self._gif_durations = []
        gif_path = resource_path("assets/images/title.gif")
        if os.path.isfile(gif_path):
            try:
                gif = Image.open(gif_path)
                gw, gh = gif.size
                nh = 60; nw = int(gw * nh / gh)
                while True:
                    f = gif.copy().convert("RGBA").resize((nw, nh), Image.LANCZOS)
                    self._gif_frames.append(ImageTk.PhotoImage(f))
                    self._gif_durations.append(gif.info.get("duration", 100))
                    gif.seek(gif.tell() + 1)
            except EOFError:
                pass

    def _load_btn_gif(self, key, filename, target_h=48):
        """Load a button GIF scaled to target_h px tall. Returns True if loaded."""
        path = resource_path(filename)
        if not os.path.isfile(path):
            return False
        frames = []; durations = []
        try:
            gif = Image.open(path)
            gw, gh = gif.size
            nw = int(gw * target_h / gh)
            while True:
                f = gif.copy().convert("RGBA").resize((nw, target_h), Image.LANCZOS)
                frames.append(ImageTk.PhotoImage(f))
                durations.append(gif.info.get("duration", 80))
                gif.seek(gif.tell() + 1)
        except EOFError:
            pass
        if frames:
            self._btn_gif[key] = {
                "frames": frames, "durations": durations,
                "index": 0, "after_id": None, "label": None
            }
            return True
        return False

    def _start_btn_gif(self, key):
        d = self._btn_gif.get(key)
        if d and d["label"]:
            self._animate_btn_gif(key)

    def _animate_btn_gif(self, key):
        d = self._btn_gif.get(key)
        if not d or not d["label"]:
            return
        frame = d["frames"][d["index"]]
        d["label"].config(image=frame)
        d["label"].image = frame           # hard ref prevents GC flicker
        delay = d["durations"][d["index"]]
        d["index"] = (d["index"] + 1) % len(d["frames"])
        d["after_id"] = self.after(delay, self._animate_btn_gif, key)

    # ------------------------------------------------------------------
    # UI build
    # ------------------------------------------------------------------

    def _build_ui(self):
        # Header
        self.header = tk.Frame(self, bd=0)
        self.header.pack(fill="x")
        header_inner = tk.Frame(self.header)
        header_inner.pack(fill="x", padx=10, pady=6)

        self.lbl_cat = tk.Label(header_inner, image=self._cat_photo, bd=0)
        if self._cat_photo:
            self.lbl_cat.pack(side="left", padx=(0, 6))

        self.btn_toggle = tk.Button(
            header_inner, text="🌙", font=("Segoe UI Emoji", 14),
            relief="flat", cursor="hand2", bd=0, width=2,
            command=self._toggle_theme)
        self.btn_toggle.pack(side="right", padx=(6, 0))

        self._muted = False
        self.btn_mute = tk.Button(
            header_inner, text="🔊", font=("Segoe UI Emoji", 14),
            relief="flat", cursor="hand2", bd=0,
            command=self._toggle_mute)
        self.btn_mute.pack(side="right", padx=(0, 2))

        self.lbl_gif = tk.Label(header_inner, bd=0, highlightthickness=0)
        if self._gif_frames:
            self.lbl_gif.configure(image=self._gif_frames[0])
        self.lbl_gif.pack(side="left", fill="x", expand=True)

        # Notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(padx=16, pady=(0, 16), fill="both", expand=True)

        self.tab_single   = tk.Frame(self.notebook, bd=0)
        self.tab_bulk     = tk.Frame(self.notebook, bd=0)
        self.tab_playlist = tk.Frame(self.notebook, bd=0)
        self.notebook.add(self.tab_single,   text="  Single Download  ")
        self.notebook.add(self.tab_bulk,     text="  Bulk Download  ")
        self.notebook.add(self.tab_playlist, text="  Playlist Download  ")

        self._build_single_tab()
        self._build_bulk_tab()
        self._build_playlist_tab()

    # ── helper: GIF button ────────────────────────────────────────────

    def _make_gif_btn(self, parent, key, gif_file, fallback_text, command, height=48):
        """
        Uses a plain tk.Label (no Button) for the GIF — zero hover flash.
        When disabled, a semi-transparent grey overlay label covers the GIF.
        Falls back to a styled tk.Button when no GIF is present.
        """
        loaded = self._load_btn_gif(key, gif_file, target_h=height)

        wrapper = tk.Frame(parent, height=height + 10, bd=0, highlightthickness=0)
        wrapper.pack_propagate(False)

        _bg = "#FFFFFF"

        if loaded:
            d = self._btn_gif[key]
            lbl = tk.Label(wrapper, image=d["frames"][0],
                           bd=0, highlightthickness=0, cursor="hand2", bg=_bg)
            lbl.place(relx=0, rely=0, relwidth=1, relheight=1)
            lbl.bind("<Button-1>", lambda e, k=key: self._gif_btn_click(k, command))
            d["label"] = lbl
            d["wrapper"] = wrapper
            d["command"] = command
            d["enabled"] = True
            # Overlay label for disabled state (hidden by default)
            overlay = tk.Label(wrapper, bg="#888888", bd=0, highlightthickness=0)
            overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
            overlay.place_forget()
            d["overlay"] = overlay
            self.after(100, self._start_btn_gif, key)
            btn = lbl
        else:
            btn = tk.Button(wrapper, text=fallback_text, relief="flat", cursor="hand2",
                            bd=0, highlightthickness=0, command=command,
                            font=("Segoe UI", 11, "bold"),
                            fg="white", activeforeground="white",
                            bg="#CC3300", activebackground="#AA2200")
            btn.pack(fill="both", expand=True)

        self._btn_gif.setdefault(key, {})["wrapper"] = wrapper
        return btn

    def _gif_btn_click(self, key, command):
        d = self._btn_gif.get(key, {})
        if d.get("enabled", True):
            command()

    def _set_gif_btn_state(self, key, enabled):
        d = self._btn_gif.get(key)
        if not d:
            return
        d["enabled"] = enabled
        overlay = d.get("overlay")
        lbl = d.get("label")
        if overlay:
            if enabled:
                overlay.place_forget()
                if lbl: lbl.configure(cursor="hand2")
            else:
                overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
                if lbl: lbl.configure(cursor="")
        else:
            # fallback text button
            wrapper = d.get("wrapper")
            if wrapper:
                for w in wrapper.winfo_children():
                    if isinstance(w, tk.Button):
                        w.configure(state="normal" if enabled else "disabled")

    # ── Single tab ────────────────────────────────────────────────────

    def _build_single_tab(self):
        p = self.tab_single

        self._lbl(p, "Video URL")
        url_row = tk.Frame(p)
        url_row.pack(fill="x", padx=16, pady=(0, 4))

        self.url_var   = tk.StringVar()
        self.url_entry = tk.Entry(url_row, textvariable=self.url_var,
                                  font=("Segoe UI", 10), relief="flat",
                                  highlightthickness=1)
        self.url_entry.pack(side="left", fill="x", expand=True, ipady=5)

        self.btn_paste = tk.Button(url_row, text="Paste", font=("Segoe UI", 9),
                                   relief="flat", cursor="hand2",
                                   command=self._paste_url)
        self.btn_paste.pack(side="left", padx=(6, 0), ipady=4, ipadx=6)

        fq_frame  = tk.Frame(p); fq_frame.pack(fill="x", padx=16, pady=(0, 4))
        left_col  = tk.Frame(fq_frame); left_col.pack(side="left", fill="x", expand=True, padx=(0,8))
        right_col = tk.Frame(fq_frame); right_col.pack(side="left", fill="x", expand=True)

        self._inline_lbl(left_col, "Format")
        self.format_var = tk.StringVar(value="Video + Audio")
        self.fmt_box = ttk.Combobox(left_col, textvariable=self.format_var,
                                    state="readonly", font=("Segoe UI", 9),
                                    values=list(QUALITY_OPTIONS.keys()), width=16)
        self.fmt_box.pack(fill="x", pady=(0, 2))
        self.fmt_box.bind("<<ComboboxSelected>>", self._on_format_change)

        self._inline_lbl(right_col, "Quality")
        self.quality_var = tk.StringVar(value="Best")
        self.qual_box = ttk.Combobox(right_col, textvariable=self.quality_var,
                                     state="readonly", font=("Segoe UI", 9),
                                     values=QUALITY_OPTIONS["Video + Audio"], width=16)
        self.qual_box.pack(fill="x", pady=(0, 2))

        self._lbl(p, "Save to folder")
        folder_row = tk.Frame(p); folder_row.pack(fill="x", padx=16, pady=(0, 4))
        self.dir_var = tk.StringVar(value=self._download_dir)
        self.folder_entry = tk.Entry(folder_row, textvariable=self.dir_var,
                                     font=("Segoe UI", 9), relief="flat",
                                     highlightthickness=1, state="readonly", width=36)
        self.folder_entry.pack(side="left", fill="x", expand=True, ipady=4)
        self.btn_browse = tk.Button(folder_row, text="Browse…", font=("Segoe UI", 9),
                                    relief="flat", cursor="hand2",
                                    command=self._browse_folder)
        self.btn_browse.pack(side="left", padx=(6, 0), ipady=4, ipadx=6)

        # GIF download button
        self.dl_btn = self._make_gif_btn(p, "single", "assets/images/download.gif",
                                         "⬇  Download", self._start_download)
        self._btn_gif["single"]["wrapper"].pack(fill="x", padx=16, pady=(12, 4))

        self.progress = ttk.Progressbar(p, mode="indeterminate")
        self.progress.pack(fill="x", padx=16, pady=(0, 4))

        self.status_var = tk.StringVar(value="Ready.")
        self.lbl_status = tk.Label(p, textvariable=self.status_var,
                                   font=("Segoe UI", 8), wraplength=440, justify="left")
        self.lbl_status.pack(anchor="w", padx=16, pady=(0, 6))

        self._lbl(p, "Output log")
        self.log = tk.Text(p, height=8, font=("Consolas", 8),
                           relief="flat", state="disabled", wrap="word")
        self.log.pack(fill="x", padx=16, pady=(0, 8))

        self.lbl_credit = tk.Label(p, text=CREDIT_TEXT,
                                   font=("Segoe UI", 7), anchor="e")
        self.lbl_credit.pack(fill="x", padx=16, pady=(0, 8), anchor="e")

    # ── Bulk tab ──────────────────────────────────────────────────────

    def _build_bulk_tab(self):
        p = self.tab_bulk

        info = tk.Label(p, text="Paste one URL per line, then click Start Bulk Download.",
                        font=("Segoe UI", 9), anchor="w")
        info.pack(anchor="w", padx=16, pady=(10, 4))
        self._bulk_info_lbl = info

        txt_frame = tk.Frame(p); txt_frame.pack(fill="both", expand=True, padx=16, pady=(0,6))
        self.bulk_text = tk.Text(txt_frame, height=8, font=("Consolas", 9),
                                 relief="flat", wrap="none")
        scrollb = ttk.Scrollbar(txt_frame, command=self.bulk_text.yview)
        self.bulk_text.configure(yscrollcommand=scrollb.set)
        self.bulk_text.pack(side="left", fill="both", expand=True)
        scrollb.pack(side="right", fill="y")

        fq2 = tk.Frame(p); fq2.pack(fill="x", padx=16, pady=(0, 4))
        lc2 = tk.Frame(fq2); lc2.pack(side="left", fill="x", expand=True, padx=(0,8))
        rc2 = tk.Frame(fq2); rc2.pack(side="left", fill="x", expand=True)

        self._inline_lbl(lc2, "Format")
        self.bulk_format_var = tk.StringVar(value="Video + Audio")
        self.bulk_fmt_box = ttk.Combobox(lc2, textvariable=self.bulk_format_var,
                                         state="readonly", font=("Segoe UI", 9),
                                         values=list(QUALITY_OPTIONS.keys()), width=16)
        self.bulk_fmt_box.pack(fill="x", pady=(0, 2))
        self.bulk_fmt_box.bind("<<ComboboxSelected>>", self._on_bulk_format_change)

        self._inline_lbl(rc2, "Quality")
        self.bulk_quality_var = tk.StringVar(value="Best")
        self.bulk_qual_box = ttk.Combobox(rc2, textvariable=self.bulk_quality_var,
                                          state="readonly", font=("Segoe UI", 9),
                                          values=QUALITY_OPTIONS["Video + Audio"], width=16)
        self.bulk_qual_box.pack(fill="x", pady=(0, 2))

        folder_row2 = tk.Frame(p); folder_row2.pack(fill="x", padx=16, pady=(0, 4))
        self.bulk_dir_var = tk.StringVar(value=self._download_dir)
        bulk_folder_entry = tk.Entry(folder_row2, textvariable=self.bulk_dir_var,
                                     font=("Segoe UI", 9), relief="flat",
                                     highlightthickness=1, state="readonly", width=36)
        bulk_folder_entry.pack(side="left", fill="x", expand=True, ipady=4)
        self._bulk_folder_entry = bulk_folder_entry

        btn_browse2 = tk.Button(folder_row2, text="Browse…", font=("Segoe UI", 9),
                                relief="flat", cursor="hand2",
                                command=self._bulk_browse_folder)
        btn_browse2.pack(side="left", padx=(6, 0), ipady=4, ipadx=6)
        self._bulk_btn_browse = btn_browse2

        # GIF download button
        self.bulk_dl_btn = self._make_gif_btn(p, "bulk", "assets/images/download2.gif",
                                              "⬇  Start Bulk Download", self._start_bulk)
        self._btn_gif["bulk"]["wrapper"].pack(fill="x", padx=16, pady=(8, 4))

        self.bulk_progress = ttk.Progressbar(p, mode="determinate")
        self.bulk_progress.pack(fill="x", padx=16, pady=(0, 4))

        list_frame = tk.Frame(p); list_frame.pack(fill="both", expand=True, padx=16, pady=(0,4))
        self.bulk_listbox = tk.Listbox(list_frame, font=("Consolas", 8),
                                       relief="flat", selectmode="browse",
                                       activestyle="none", height=6)
        sb2 = ttk.Scrollbar(list_frame, command=self.bulk_listbox.yview)
        self.bulk_listbox.configure(yscrollcommand=sb2.set)
        self.bulk_listbox.pack(side="left", fill="both", expand=True)
        sb2.pack(side="right", fill="y")

        self.bulk_status_var = tk.StringVar(value="")
        self._bulk_status_lbl = tk.Label(p, textvariable=self.bulk_status_var,
                                          font=("Segoe UI", 8), anchor="w")
        self._bulk_status_lbl.pack(anchor="w", padx=16, pady=(0, 8))

        self.bulk_lbl_credit = tk.Label(p, text=CREDIT_TEXT,
                                 font=("Segoe UI", 7), anchor="e")
        self.bulk_lbl_credit.pack(fill="x", padx=16, pady=(0, 8))

    # ── Playlist tab ──────────────────────────────────────────────────

    def _build_playlist_tab(self):
        p = self.tab_playlist

        info = tk.Label(p, text="Paste a playlist URL, fetch its videos, then download all.",
                        font=("Segoe UI", 9), anchor="w")
        info.pack(anchor="w", padx=16, pady=(10, 4))
        self._pl_info_lbl = info

        url_row = tk.Frame(p); url_row.pack(fill="x", padx=16, pady=(0, 6))
        self.pl_url_var   = tk.StringVar()
        self.pl_url_entry = tk.Entry(url_row, textvariable=self.pl_url_var,
                                     font=("Segoe UI", 10), relief="flat",
                                     highlightthickness=1)
        self.pl_url_entry.pack(side="left", fill="x", expand=True, ipady=5)

        self.pl_btn_paste = tk.Button(url_row, text="Paste", font=("Segoe UI", 9),
                                      relief="flat", cursor="hand2",
                                      command=self._pl_paste_url)
        self.pl_btn_paste.pack(side="left", padx=(6, 0), ipady=4, ipadx=6)

        self.pl_btn_fetch = tk.Button(url_row, text="🔍 Fetch", font=("Segoe UI", 9),
                                      relief="flat", cursor="hand2",
                                      command=self._pl_fetch)
        self.pl_btn_fetch.pack(side="left", padx=(6, 0), ipady=4, ipadx=6)

        fq = tk.Frame(p); fq.pack(fill="x", padx=16, pady=(0, 4))
        lc = tk.Frame(fq); lc.pack(side="left", fill="x", expand=True, padx=(0,8))
        rc = tk.Frame(fq); rc.pack(side="left", fill="x", expand=True)

        self._inline_lbl(lc, "Format")
        self.pl_format_var = tk.StringVar(value="Video + Audio")
        self.pl_fmt_box = ttk.Combobox(lc, textvariable=self.pl_format_var,
                                        state="readonly", font=("Segoe UI", 9),
                                        values=list(QUALITY_OPTIONS.keys()), width=16)
        self.pl_fmt_box.pack(fill="x", pady=(0, 2))
        self.pl_fmt_box.bind("<<ComboboxSelected>>", self._on_pl_format_change)

        self._inline_lbl(rc, "Quality")
        self.pl_quality_var = tk.StringVar(value="Best")
        self.pl_qual_box = ttk.Combobox(rc, textvariable=self.pl_quality_var,
                                         state="readonly", font=("Segoe UI", 9),
                                         values=QUALITY_OPTIONS["Video + Audio"], width=16)
        self.pl_qual_box.pack(fill="x", pady=(0, 2))

        folder_row = tk.Frame(p); folder_row.pack(fill="x", padx=16, pady=(0, 4))
        self.pl_dir_var = tk.StringVar(value=self._download_dir)
        pl_folder_entry = tk.Entry(folder_row, textvariable=self.pl_dir_var,
                                   font=("Segoe UI", 9), relief="flat",
                                   highlightthickness=1, state="readonly", width=36)
        pl_folder_entry.pack(side="left", fill="x", expand=True, ipady=4)
        self._pl_folder_entry = pl_folder_entry

        pl_btn_browse = tk.Button(folder_row, text="Browse…", font=("Segoe UI", 9),
                                  relief="flat", cursor="hand2",
                                  command=self._pl_browse_folder)
        pl_btn_browse.pack(side="left", padx=(6, 0), ipady=4, ipadx=6)
        self._pl_btn_browse = pl_btn_browse

        # GIF download button
        self.pl_dl_btn = self._make_gif_btn(p, "playlist", "assets/images/download3.gif",
                                            "⬇  Download Playlist", self._pl_start)
        self._btn_gif["playlist"]["wrapper"].pack(fill="x", padx=16, pady=(8, 4))
        #self._set_gif_btn_state("playlist", False)

        self.pl_progress = ttk.Progressbar(p, mode="determinate")
        self.pl_progress.pack(fill="x", padx=16, pady=(0, 4))

        list_frame = tk.Frame(p); list_frame.pack(fill="both", expand=True, padx=16, pady=(0,4))
        self.pl_listbox = tk.Listbox(list_frame, font=("Consolas", 8),
                                     relief="flat", selectmode="browse",
                                     activestyle="none", height=7)
        sb = ttk.Scrollbar(list_frame, command=self.pl_listbox.yview)
        self.pl_listbox.configure(yscrollcommand=sb.set)
        self.pl_listbox.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self.pl_status_var = tk.StringVar(value="")
        self._pl_status_lbl = tk.Label(p, textvariable=self.pl_status_var,
                                        font=("Segoe UI", 8), anchor="w")
        self._pl_status_lbl.pack(anchor="w", padx=16, pady=(0, 8))

        self.pl_lbl_credit = tk.Label(p, text=CREDIT_TEXT,
                              font=("Segoe UI", 7), anchor="e")
        self.pl_lbl_credit.pack(fill="x", padx=16, pady=(0, 8))

    # ------------------------------------------------------------------
    # Label helpers
    # ------------------------------------------------------------------

    def _lbl(self, parent, text):
        lbl = tk.Label(parent, text=text, font=("Segoe UI", 9), anchor="w")
        lbl.pack(anchor="w", padx=16, pady=(10, 2))
        return lbl

    def _inline_lbl(self, parent, text):
        lbl = tk.Label(parent, text=text, font=("Segoe UI", 9), anchor="w")
        lbl.pack(anchor="w", pady=(4, 2))
        return lbl

    # ------------------------------------------------------------------
    # Title GIF animation
    # ------------------------------------------------------------------

    def _start_gif(self):
        if self._gif_frames:
            self._animate_gif()

    def _animate_gif(self):
        if not self._gif_frames:
            return
        frame = self._gif_frames[self._gif_index]
        self.lbl_gif.config(image=frame)
        self.lbl_gif.image = frame          # hard ref prevents GC flicker
        delay = self._gif_durations[self._gif_index] if self._gif_durations else 100
        self._gif_index = (self._gif_index + 1) % len(self._gif_frames)
        self._after_id  = self.after(delay, self._animate_gif)

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def _toggle_mute(self):
        self._muted = not self._muted
        self.btn_mute.configure(text="🔇" if self._muted else "🔊")
        if self._muted:
            if self._music_proc:
                try:
                    self._music_proc.terminate()
                    self._music_proc = None
                except Exception:
                    pass
        else:
            self._start_music()
        self._apply_theme()  # recolor btn

    def _toggle_theme(self):
        self._theme_name = "dark" if self._theme_name == "light" else "light"
        self._apply_theme()

    def _apply_theme(self):
        t = THEMES[self._theme_name]

        self.configure(bg=t["bg"])

        # Header
        self.header.configure(bg=t["header_bg"])
        for w in self.header.winfo_children():
            w.configure(bg=t["header_bg"])
            if isinstance(w, tk.Frame):
                for ww in w.winfo_children():
                    if isinstance(ww, (tk.Label, tk.Frame)):
                        ww.configure(bg=t["header_bg"])

        self.btn_mute.configure(
            bg=t["header_bg"], fg=t["fg2"],
            activebackground=t["header_bg"], activeforeground=t["fg"])
        self.btn_toggle.configure(
            bg=t["header_bg"], fg=t["fg"],
            activebackground=t["header_bg"], activeforeground=t["fg"],
            text=t["toggle_icon"])

        # Notebook style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook",     background=t["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", background=t["btn_bg"], foreground=t["fg"],
                        padding=[10, 4])
        style.map("TNotebook.Tab",
                  background=[("selected", t["card"])],
                  foreground=[("selected", t["fg"])])

        for tab in (self.tab_single, self.tab_bulk, self.tab_playlist):
            tab.configure(bg=t["card"])
            self._recolor_frame(tab, t)

        # Single tab
        self.url_entry.configure(bg=t["entry_bg"], fg=t["fg"],
                                 highlightbackground=t["border"],
                                 insertbackground=t["fg"])
        self.btn_paste.configure(bg=t["btn_bg"], fg=t["btn_fg"],
                                 activebackground=t["border"])
        self.folder_entry.configure(bg=t["folder_bg"], fg=t["fg2"],
                                    highlightbackground=t["border"])
        self.btn_browse.configure(bg=t["btn_bg"], fg=t["btn_fg"],
                                  activebackground=t["border"])
        self.log.configure(bg=t["log_bg"], fg=t["log_fg"])
        self.lbl_credit.configure(bg=t["card"], fg=t["credit_fg"])

        # Bulk tab
        self.bulk_text.configure(bg=t["log_bg"], fg=t["log_fg"],
                                 insertbackground=t["log_fg"])
        self._bulk_folder_entry.configure(bg=t["folder_bg"], fg=t["fg2"],
                                          highlightbackground=t["border"])
        self._bulk_btn_browse.configure(bg=t["btn_bg"], fg=t["btn_fg"],
                                        activebackground=t["border"])
        self.bulk_listbox.configure(bg=t["list_bg"], fg=t["fg"],
                                    selectbackground=t["list_sel"],
                                    selectforeground=t["list_sel_fg"])
        if hasattr(self, "bulk_lbl_credit"):
            self.bulk_lbl_credit.configure(bg=t["card"], fg=t["credit_fg"])

        # Playlist tab
        self.pl_url_entry.configure(bg=t["entry_bg"], fg=t["fg"],
                                    highlightbackground=t["border"],
                                    insertbackground=t["fg"])
        self.pl_btn_paste.configure(bg=t["btn_bg"], fg=t["btn_fg"],
                                    activebackground=t["border"])
        self.pl_btn_fetch.configure(bg=t["btn_bg"], fg=t["btn_fg"],
                                    activebackground=t["border"])
        self._pl_folder_entry.configure(bg=t["folder_bg"], fg=t["fg2"],
                                        highlightbackground=t["border"])
        self._pl_btn_browse.configure(bg=t["btn_bg"], fg=t["btn_fg"],
                                      activebackground=t["border"])
        self.pl_listbox.configure(bg=t["list_bg"], fg=t["fg"],
                                  selectbackground=t["list_sel"],
                                  selectforeground=t["list_sel_fg"])
        if hasattr(self, "pl_lbl_credit"):
            self.pl_lbl_credit.configure(bg=t["card"], fg=t["credit_fg"])

        # GIF buttons: sync bg to card so no colour flashes on hover
        btn_names = {"single": "dl_btn", "bulk": "bulk_dl_btn", "playlist": "pl_dl_btn"}
        for key in ("single", "bulk", "playlist"):
            d = self._btn_gif.get(key)
            if not d:
                continue
            wrapper = d.get("wrapper")
            if wrapper:
                try: wrapper.configure(bg=t["card"])
                except Exception: pass
            lbl = d.get("label")
            if lbl:
                try: lbl.configure(bg=t["card"])
                except Exception: pass
            else:
                # fallback text button
                btn = getattr(self, btn_names.get(key, ""), None)
                if btn:
                    try:
                        btn.configure(bg=t["accent"], activebackground=t["accent_hov"],
                                      fg="white", activeforeground="white")
                    except Exception: pass

        # Combobox — key fix: force visible field bg and fg in dark mode
        style.configure("TCombobox",
                        fieldbackground=t["combo_field"],
                        background=t["btn_bg"],
                        foreground=t["combo_fg"],
                        selectbackground=t["accent"],
                        selectforeground="white",
                        bordercolor=t["border"],
                        arrowcolor=t["combo_fg"])
        style.map("TCombobox",
                  fieldbackground=[("readonly", t["combo_field"])],
                  foreground=[("readonly", t["combo_fg"])],
                  selectbackground=[("readonly", t["accent"])],
                  selectforeground=[("readonly", "white")])

        style.configure("Horizontal.TProgressbar",
                        troughcolor=t["btn_bg"], background=t["accent"])

    def _recolor_frame(self, fr, t):
        try:
            fr.configure(bg=t["card"])
        except Exception:
            pass
        for w in fr.winfo_children():
            if isinstance(w, tk.Label):
                w.configure(bg=t["card"], fg=t["fg2"])
            elif isinstance(w, tk.Frame):
                self._recolor_frame(w, t)

    # ------------------------------------------------------------------
    # Format / quality
    # ------------------------------------------------------------------

    def _on_format_change(self, event=None):
        fmt = self.format_var.get()
        opts = QUALITY_OPTIONS[fmt]
        self.qual_box["values"] = opts; self.quality_var.set(opts[0])
        self.qual_box.configure(state="disabled" if fmt == "Audio" else "readonly")

    def _on_bulk_format_change(self, event=None):
        fmt = self.bulk_format_var.get()
        opts = QUALITY_OPTIONS[fmt]
        self.bulk_qual_box["values"] = opts; self.bulk_quality_var.set(opts[0])
        self.bulk_qual_box.configure(state="disabled" if fmt == "Audio" else "readonly")

    def _on_pl_format_change(self, event=None):
        fmt = self.pl_format_var.get()
        opts = QUALITY_OPTIONS[fmt]
        self.pl_qual_box["values"] = opts; self.pl_quality_var.set(opts[0])
        self.pl_qual_box.configure(state="disabled" if fmt == "Audio" else "readonly")

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def _check_ytdlp(self):
        if not find_ytdlp():
            messagebox.showwarning(
                "yt-dlp not found",
                "yt-dlp.exe was not found.\n\n"
                "Place yt-dlp.exe in the same folder as this app,\n"
                "or install via: winget install yt-dlp")

    def _paste_url(self):
        try: self.url_var.set(self.clipboard_get().strip())
        except tk.TclError: pass

    def _browse_folder(self):
        f = filedialog.askdirectory(initialdir=self._download_dir)
        if f: self._download_dir = f; self.dir_var.set(f)

    def _bulk_browse_folder(self):
        f = filedialog.askdirectory(initialdir=self._download_dir)
        if f: self._download_dir = f; self.bulk_dir_var.set(f)

    def _pl_paste_url(self):
        try: self.pl_url_var.set(self.clipboard_get().strip())
        except tk.TclError: pass

    def _pl_browse_folder(self):
        f = filedialog.askdirectory(initialdir=self._download_dir)
        if f: self._download_dir = f; self.pl_dir_var.set(f)

    def _log(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _set_status(self, text):
        self.status_var.set(text)

    def _on_close(self):
        self._closing = True

        try:
            if self._music_proc:
                self._music_proc.terminate()
                self._music_proc.kill()   # <-- important
                self._music_proc = None
        except Exception:
            pass

        self.destroy()

    # ------------------------------------------------------------------
    # Download command builder
    # ------------------------------------------------------------------

    def _build_command(self, url, out_dir, fmt=None, quality=None):
        ytdlp = find_ytdlp()
        if not ytdlp:
            raise FileNotFoundError("yt-dlp executable not found.")
        fmt     = fmt     or self.format_var.get()
        quality = quality or self.quality_var.get()
        cmd = [ytdlp, "--newline", "-o",
               os.path.join(out_dir, "%(title)s.%(ext)s")]
        if fmt == "Audio":
            cmd += ["-x", "--audio-format", "mp3", "--audio-quality", "0"]
        elif fmt == "Video":
            if quality == "Best":
                cmd += ["-f", "bestvideo"]
            else:
                h = quality.replace("p","")
                cmd += ["-f", f"bestvideo[height<={h}]"]
        else:
            if quality == "Best":
                cmd += ["-f", "bestvideo+bestaudio/best", "--merge-output-format", "mp4"]
            else:
                h = quality.replace("p","")
                cmd += ["-f", f"bestvideo[height<={h}]+bestaudio/best[height<={h}]",
                        "--merge-output-format", "mp4"]
        cmd.append(url)
        return cmd

    # ------------------------------------------------------------------
    # Single download
    # ------------------------------------------------------------------

    def _start_download(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("No URL", "Please paste a YouTube URL first.")
            return
        out_dir = self.dir_var.get().strip() or self._download_dir
        os.makedirs(out_dir, exist_ok=True)
        try:
            cmd = self._build_command(url, out_dir)
        except FileNotFoundError as e:
            messagebox.showerror("Error", str(e)); return

        self._set_gif_btn_state("single", False)
        self.progress.start(10)
        self._set_status("Starting download…")
        self._log("$ " + " ".join(cmd))
        threading.Thread(target=self._run, args=(cmd,), daemon=True).start()

    def _run(self, cmd):
        try:
            self._process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)
            for line in self._process.stdout:
                line = line.rstrip()
                if line:
                    self.after(0, self._log, line)
                    if "[download]" in line:
                        self.after(0, self._set_status, line)
            self._process.wait()
            rc = self._process.returncode
            if rc == 0: self.after(0, self._on_done, True,  "Download complete!")
            else:       self.after(0, self._on_done, False, f"yt-dlp exited with code {rc}.")
        except Exception as e:
            self.after(0, self._on_done, False, f"Error: {e}")

    def _on_done(self, success, msg):
        self.progress.stop()
        self._set_gif_btn_state("single", True)
        self._set_status(msg); self._log(msg)
        if success: messagebox.showinfo("Done!", msg + f"\n\nSaved to: {self.dir_var.get()}")
        else:       messagebox.showerror("Failed", msg)

    # ------------------------------------------------------------------
    # Bulk download
    # ------------------------------------------------------------------

    def _start_bulk(self):
        if self._bulk_running: return
        raw  = self.bulk_text.get("1.0","end").strip()
        urls = [u.strip() for u in raw.splitlines() if u.strip()]
        if not urls:
            messagebox.showwarning("No URLs","Please paste at least one URL."); return
        out_dir = self.bulk_dir_var.get().strip() or self._download_dir
        os.makedirs(out_dir, exist_ok=True)
        self._bulk_queue = urls; self._bulk_index = 0
        self._bulk_running = True; self._bulk_out_dir = out_dir
        self.bulk_listbox.delete(0,"end")
        for u in urls: self.bulk_listbox.insert("end", f"⏳  {u}")
        self.bulk_progress.configure(maximum=len(urls), value=0)
        self._set_gif_btn_state("bulk", False)
        self._bulk_next()

    def _bulk_next(self):
        if self._bulk_index >= len(self._bulk_queue):
            self._bulk_done_all(); return
        url = self._bulk_queue[self._bulk_index]
        self._bulk_update_row(self._bulk_index, f"⬇  {url}")
        self.bulk_listbox.see(self._bulk_index)
        self.bulk_status_var.set(f"Downloading {self._bulk_index+1}/{len(self._bulk_queue)} …")
        fmt = self.bulk_format_var.get(); quality = self.bulk_quality_var.get()
        try:
            cmd = self._build_command(url, self._bulk_out_dir, fmt, quality)
        except FileNotFoundError as e:
            self._bulk_update_row(self._bulk_index, f"❌  {url}  ({e})")
            self._bulk_advance(False); return
        threading.Thread(target=self._bulk_run,
                         args=(cmd, url, self._bulk_index), daemon=True).start()

    def _bulk_run(self, cmd, url, idx):
        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)
            for _ in proc.stdout: pass
            proc.wait(); success = proc.returncode == 0
        except Exception: success = False
        self.after(0, self._bulk_item_done, idx, url, success)

    def _bulk_item_done(self, idx, url, success):
        self._bulk_update_row(idx, f"{'✅' if success else '❌'}  {url}")
        self.bulk_progress.configure(value=idx+1)
        self._bulk_advance(success)

    def _bulk_advance(self, _):
        self._bulk_index += 1; self._bulk_next()

    def _bulk_done_all(self):
        self._bulk_running = False
        self._set_gif_btn_state("bulk", True)
        total = len(self._bulk_queue)
        ok = sum(1 for i in range(self.bulk_listbox.size())
                 if self.bulk_listbox.get(i).startswith("✅"))
        self.bulk_status_var.set(f"Done! {ok}/{total} succeeded. Saved to: {self._bulk_out_dir}")
        messagebox.showinfo("Bulk Download Done",
                            f"{ok} of {total} downloads succeeded.\n\nSaved to: {self._bulk_out_dir}")

    def _bulk_update_row(self, idx, text):
        self.bulk_listbox.delete(idx); self.bulk_listbox.insert(idx, text)

    # ------------------------------------------------------------------
    # Playlist download
    # ------------------------------------------------------------------

    def _pl_fetch(self):
        url = self.pl_url_var.get().strip()
        if not url:
            messagebox.showwarning("No URL","Please paste a playlist URL first."); return
        if self._pl_running: return
        self.pl_btn_fetch.configure(state="disabled", text="Fetching…")
        #self._set_gif_btn_state("playlist", False)
        self.pl_listbox.delete(0,"end")
        self.pl_status_var.set("Fetching playlist info…")
        self._pl_queue = []
        threading.Thread(target=self._pl_do_fetch, args=(url,), daemon=True).start()

    def _pl_do_fetch(self, url):
        ytdlp = find_ytdlp()
        if not ytdlp:
            self.after(0, self._pl_fetch_done, [], "yt-dlp not found."); return
        cmd = [ytdlp, "--flat-playlist", "--print", "url", "--yes-playlist", url]
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    text=True,
                                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)
            stdout, _ = proc.communicate()
            urls = [u.strip() for u in stdout.splitlines() if u.strip()]
            if urls: self.after(0, self._pl_fetch_done, urls, f"Found {len(urls)} video(s).")
            else:    self.after(0, self._pl_fetch_done, [], "No videos found. Valid playlist URL?")
        except Exception as e:
            self.after(0, self._pl_fetch_done, [], f"Error: {e}")

    def _pl_fetch_done(self, urls, msg):
        self.pl_btn_fetch.configure(state="normal", text="🔍 Fetch")
        self.pl_status_var.set(msg)
        if not urls: return
        self._pl_queue = urls
        self.pl_listbox.delete(0,"end")
        for u in urls: self.pl_listbox.insert("end", f"⏳  {u}")
        self.pl_progress.configure(maximum=len(urls), value=0)
        self._set_gif_btn_state("playlist", True)

    def _pl_start(self):
        if self._pl_running or not self._pl_queue: return
        out_dir = self.pl_dir_var.get().strip() or self._download_dir
        os.makedirs(out_dir, exist_ok=True)
        self._pl_out_dir = out_dir; self._pl_index = 0; self._pl_running = True
        #self._set_gif_btn_state("playlist", False)
        self.pl_btn_fetch.configure(state="disabled")
        self._pl_next()

    def _pl_next(self):
        if self._pl_index >= len(self._pl_queue):
            self._pl_done_all(); return
        url = self._pl_queue[self._pl_index]
        self._pl_update_row(self._pl_index, f"⬇  {url}")
        self.pl_listbox.see(self._pl_index)
        self.pl_status_var.set(f"Downloading {self._pl_index+1}/{len(self._pl_queue)} …")
        fmt = self.pl_format_var.get(); quality = self.pl_quality_var.get()
        try:
            cmd = self._build_command(url, self._pl_out_dir, fmt, quality)
        except FileNotFoundError as e:
            self._pl_update_row(self._pl_index, f"❌  {url}  ({e})")
            self._pl_index += 1; self._pl_next(); return
        threading.Thread(target=self._pl_run,
                         args=(cmd, url, self._pl_index), daemon=True).start()

    def _pl_run(self, cmd, url, idx):
        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)
            for _ in proc.stdout: pass
            proc.wait(); success = proc.returncode == 0
        except Exception: success = False
        self.after(0, self._pl_item_done, idx, url, success)

    def _pl_item_done(self, idx, url, success):
        self._pl_update_row(idx, f"{'✅' if success else '❌'}  {url}")
        self.pl_progress.configure(value=idx+1)
        self._pl_index += 1; self._pl_next()

    def _pl_done_all(self):
        self._pl_running = False
        self._set_gif_btn_state("playlist", True)
        self.pl_btn_fetch.configure(state="normal", text="🔍 Fetch")
        total = len(self._pl_queue)
        ok = sum(1 for i in range(self.pl_listbox.size())
                 if self.pl_listbox.get(i).startswith("✅"))
        self.pl_status_var.set(f"Done! {ok}/{total} succeeded. Saved to: {self._pl_out_dir}")
        messagebox.showinfo("Playlist Download Done",
                            f"{ok} of {total} videos downloaded.\n\nSaved to: {self._pl_out_dir}")

    def _pl_update_row(self, idx, text):
        self.pl_listbox.delete(idx); self.pl_listbox.insert(idx, text)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = App()
    app.mainloop()
