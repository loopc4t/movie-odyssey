"""
ui.py — Movie Odyssey TUI
Psychotronic cult-cinema terminal interface built on curses.
"""

import curses
import os
import subprocess
import textwrap
from typing import Any

# ─── SOUND ────────────────────────────────────────────────────────────────────

# click.mp3 lives next to this script
_CLICK_SOUND = os.path.join(os.path.dirname(os.path.abspath(__file__)), "click.mp3")

# Persistent mpg123 process in remote-control mode.
# We write "LOAD <file>\n" to its stdin — eliminates per-keypress startup cost.
_mpg123_proc = None


def _start_mpg123():
    try:
        return subprocess.Popen(
            ["mpg123", "-q", "--remote"],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        return None


def play_click() -> None:
    """Send LOAD to the persistent mpg123 server — near-zero latency."""
    global _mpg123_proc
    if not os.path.isfile(_CLICK_SOUND):
        return
    if _mpg123_proc is None or _mpg123_proc.poll() is not None:
        _mpg123_proc = _start_mpg123()
    if _mpg123_proc is None:
        return
    try:
        _mpg123_proc.stdin.write(f"LOAD {_CLICK_SOUND}\n".encode())
        _mpg123_proc.stdin.flush()
    except (BrokenPipeError, OSError):
        _mpg123_proc = None


def stop_click_server() -> None:
    """Shut down the mpg123 server cleanly on exit."""
    global _mpg123_proc
    if _mpg123_proc and _mpg123_proc.poll() is None:
        try:
            _mpg123_proc.stdin.write(b"QUIT\n")
            _mpg123_proc.stdin.flush()
        except OSError:
            pass
        _mpg123_proc = None


from library import scan_movies
from nfo_parser import parse_nfo
from player import play_movie


# ─── COLOUR PAIRS ─────────────────────────────────────────────────────────────

C_NORMAL     = 1
C_TITLE_BAR  = 2
C_STATUS_BAR = 3
C_SELECTED   = 4
C_ACCENT     = 5
C_DIM        = 6
C_PLAY_BTN   = 7
C_BORDER     = 8
C_SEARCH     = 9
C_WARN       = 10
C_SPLATTER   = 11


def init_colors() -> None:
    curses.start_color()
    curses.use_default_colors()

    has256 = curses.COLORS >= 256
    BG = -1

    # Psychotronic palette: near-black bg, sickly green, blood red, yellowed bone
    BLACK     = 232 if has256 else curses.COLOR_BLACK
    OFFWHITE  = 252 if has256 else curses.COLOR_WHITE
    GREY      = 244 if has256 else curses.COLOR_WHITE
    DARK_GREY = 237 if has256 else curses.COLOR_BLACK
    SLIME     = 82  if has256 else curses.COLOR_GREEN
    BILE      = 64  if has256 else curses.COLOR_GREEN
    BLOOD     = 160 if has256 else curses.COLOR_RED
    VISCERA   = 196 if has256 else curses.COLOR_RED
    BONE      = 229 if has256 else curses.COLOR_YELLOW
    MARROW    = 94  if has256 else curses.COLOR_BLACK

    curses.init_pair(C_NORMAL,     OFFWHITE,  BG)
    curses.init_pair(C_TITLE_BAR,  BONE,      MARROW)
    curses.init_pair(C_STATUS_BAR, GREY,      DARK_GREY)
    curses.init_pair(C_SELECTED,   BLACK,     SLIME)
    curses.init_pair(C_ACCENT,     SLIME,     BG)
    curses.init_pair(C_DIM,        GREY,      BG)
    curses.init_pair(C_PLAY_BTN,   BONE,      BLOOD)
    curses.init_pair(C_BORDER,     BILE,      BG)
    curses.init_pair(C_SEARCH,     SLIME,     DARK_GREY)
    curses.init_pair(C_WARN,       BLOOD,     BG)
    curses.init_pair(C_SPLATTER,   VISCERA,   BG)


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def safe_addstr(win, y: int, x: int, text: str, attr: int = 0) -> None:
    h, w = win.getmaxyx()
    if y < 0 or y >= h or x < 0 or x >= w:
        return
    max_len = w - x
    if max_len <= 0:
        return
    try:
        win.addstr(y, x, text[:max_len], attr)
    except curses.error:
        pass


def safe_addch(win, y: int, x: int, ch, attr: int = 0) -> None:
    h, w = win.getmaxyx()
    if 0 <= y < h and 0 <= x < w:
        try:
            win.addch(y, x, ch, attr)
        except curses.error:
            pass


def hline(win, y: int, x: int, length: int, attr: int = 0) -> None:
    for i in range(length):
        safe_addch(win, y, x + i, curses.ACS_HLINE, attr)


def clamp(val: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, val))


# ─── INFO PANEL RENDERER ──────────────────────────────────────────────────────

def render_info(win, movie: dict, info: dict) -> None:
    win.erase()
    h, w = win.getmaxyx()
    row = 0

    def label(text: str, value: str) -> None:
        nonlocal row
        if row >= h - 1 or not value:
            return
        lbl = f"  {text}: "
        safe_addstr(win, row, 0, lbl, curses.color_pair(C_ACCENT) | curses.A_BOLD)
        avail = w - len(lbl)
        if avail > 0:
            safe_addstr(win, row, len(lbl), value[:avail], curses.color_pair(C_NORMAL))
        row += 1

    def section(text: str) -> None:
        nonlocal row
        if row >= h - 1:
            return
        row += 1
        line = f"  -- {text.upper()} "
        safe_addstr(win, row, 0, line[:w], curses.color_pair(C_BORDER) | curses.A_BOLD)
        row += 1

    def para(text: str, indent: int = 2) -> None:
        nonlocal row
        if not text:
            return
        avail_w = max(10, w - indent - 1)
        for line in textwrap.wrap(text, avail_w):
            if row >= h - 1:
                break
            safe_addstr(win, row, indent, line, curses.color_pair(C_NORMAL))
            row += 1

    def blank() -> None:
        nonlocal row
        row += 1

    # Title
    title = info.get("title") or movie["title"]
    year  = info.get("year", "")
    headline = f"  {title}"
    if year:
        headline += f"  [{year}]"
    safe_addstr(win, row, 0, headline[:w], curses.color_pair(C_ACCENT) | curses.A_BOLD)
    row += 1

    orig = info.get("original_title", "")
    if orig and orig.lower() != title.lower():
        safe_addstr(win, row, 2, orig[:w - 2], curses.color_pair(C_DIM))
        row += 1

    tagline = info.get("tagline", "")
    if tagline:
        safe_addstr(win, row, 2, f'"{tagline}"'[:w - 2],
                    curses.color_pair(C_DIM) | curses.A_ITALIC)
        row += 1

    blank()

    label("Rating",  info.get("rating", ""))
    label("Runtime", f"{info['runtime']} min" if info.get("runtime") else "")
    label("MPAA",    info.get("mpaa", ""))
    label("Genre",   "  /  ".join(info.get("genres", [])))
    label("Country", ", ".join(info.get("countries", [])))
    label("Released",info.get("premiered", ""))
    label("Studio",  ", ".join(info.get("studios", [])))

    plot = info.get("plot") or info.get("outline", "")
    if plot:
        section("Plot")
        para(plot)

    dirs = info.get("directors", [])
    wris = info.get("writers",   [])
    if dirs or wris:
        section("Crew")
        label("Director", ", ".join(dirs))
        label("Writer",   ", ".join(wris[:4]))

    actors = info.get("actors", [])
    if actors:
        section("Cast")
        for a in actors[:12]:
            if row >= h - 1:
                break
            name  = a.get("name", "")
            role  = a.get("role", "")
            entry = f"  {name}"
            if role:
                entry += f"  --  {role}"
            safe_addstr(win, row, 0, entry[:w], curses.color_pair(C_NORMAL))
            row += 1

    fi  = info.get("file_info", {})
    vid = fi.get("video", {})
    aud = fi.get("audio", {})
    if vid or aud:
        section("File")
        if vid:
            res   = (f"{vid.get('width','')}x{vid.get('height','')}"
                     if vid.get("width") else "")
            parts = [x for x in [vid.get("codec",""), res] if x]
            label("Video", "  ".join(parts))
        if aud:
            ch    = aud.get("channels", "")
            parts = [x for x in [aud.get("codec",""),
                                  f"{ch}ch" if ch else "",
                                  aud.get("language","")] if x]
            label("Audio", "  ".join(parts))

    imdb = info.get("imdb_id", "")
    if imdb:
        blank()
        safe_addstr(win, row, 2, f"IMDb  {imdb}", curses.color_pair(C_DIM))
        row += 1

    if not info:
        blank()
        safe_addstr(win, row, 2, "[ NO SIGNAL -- no .nfo found ]",
                    curses.color_pair(C_WARN))

    win.noutrefresh()


# ─── PLAY CONFIRMATION OVERLAY ────────────────────────────────────────────────

def confirm_play(stdscr, movie: dict) -> bool:
    sh, sw = stdscr.getmaxyx()
    title  = movie["title"]
    line1  = f"  PLAY:  {title}  "
    line2  = "  [ENTER / Y] confirm    [ESC / N] abort  "
    bw     = min(sw - 4, max(46, max(len(line1), len(line2)) + 4))
    bh     = 7
    by     = sh // 2 - bh // 2
    bx     = sw // 2 - bw // 2

    box = curses.newwin(bh, bw, by, bx)
    box.erase()
    box.attron(curses.color_pair(C_BORDER))
    box.box()
    box.attroff(curses.color_pair(C_BORDER))

    header = " TRANSMISSION INCOMING "
    hx = max(0, bw // 2 - len(header) // 2)
    safe_addstr(box, 0, hx, header,
                curses.color_pair(C_TITLE_BAR) | curses.A_BOLD)
    safe_addstr(box, 2, 2, line1[:bw - 4],
                curses.color_pair(C_ACCENT) | curses.A_BOLD)
    hline(box, 4, 1, bw - 2, curses.color_pair(C_BORDER))
    safe_addstr(box, 5, 2, line2[:bw - 4], curses.color_pair(C_DIM))

    box.noutrefresh()
    curses.doupdate()

    while True:
        key = stdscr.getch()
        if key in (curses.KEY_ENTER, 10, 13, ord("y"), ord("Y")):
            return True
        if key in (27, ord("n"), ord("N"), ord("q"), ord("Q")):
            return False


# ─── MAIN TUI ─────────────────────────────────────────────────────────────────

# Single-column ASCII prefix marks — never cause wide-char column shift
_MARK_VIDEO = ">"   # has playable video
_MARK_EMPTY = " "   # no video found
_MARK_NFO   = "*"   # has NFO metadata


class MovieOdysseyApp:
    LIST_RATIO = 0.38

    def __init__(self, stdscr):
        self.stdscr      = stdscr
        self.movies:   list[dict] = []
        self.filtered: list[dict] = []
        self.cursor      = 0
        self.offset      = 0
        self.search      = ""
        self.search_mode = False
        self.count_buf   = 0    # numeric prefix accumulator (vim-style)
        self._last_key   = -1  # for gg detection
        self._info_cache: dict[str, dict] = {}

    def setup(self) -> None:
        curses.curs_set(0)
        self.stdscr.keypad(True)
        self.stdscr.timeout(-1)
        init_colors()
        self.movies   = scan_movies()
        self.filtered = list(self.movies)

    def get_info(self, movie: dict) -> dict:
        key = movie.get("nfo_path") or movie["folder"]
        if key not in self._info_cache:
            nfo = movie.get("nfo_path")
            self._info_cache[key] = parse_nfo(nfo) if nfo else {}
        return self._info_cache[key]

    def apply_filter(self) -> None:
        q = self.search.lower()
        self.filtered = (
            list(self.movies) if not q
            else [m for m in self.movies if q in m["title"].lower()]
        )
        self.cursor = 0
        self.offset = 0

    def dimensions(self):
        sh, sw = self.stdscr.getmaxyx()
        list_w = max(20, int(sw * self.LIST_RATIO))
        info_w = sw - list_w - 1
        return sh, sw, list_w, info_w

    # ── Draw routines ──────────────────────────────────────────────────────────

    def draw_title_bar(self, sh: int, sw: int) -> None:
        attr  = curses.color_pair(C_TITLE_BAR) | curses.A_BOLD
        left  = "  *** MOVIE ODYSSEY ***  "
        right = f"  {len(self.filtered)}/{len(self.movies)} titles  "
        pad   = sw - len(left) - len(right)
        line  = left + " " * max(0, pad) + right
        safe_addstr(self.stdscr, 0, 0, line[:sw], attr)

    def draw_status_bar(self, sh: int, sw: int) -> None:
        attr = curses.color_pair(C_STATUS_BAR)
        if self.search_mode:
            hint = f"  SCAN: {self.search}_   [Esc] done"
        else:
            hint = "  j/k navigate    gg top    G bottom    Ctrl+D/U half page    ENTER play    / search    q quit  "
        line = hint + " " * max(0, sw - len(hint))
        safe_addstr(self.stdscr, sh - 1, 0, line[:sw], attr)

    def draw_divider(self, sh: int, sw: int, list_w: int) -> None:
        attr = curses.color_pair(C_BORDER)
        for row in range(1, sh - 1):
            safe_addch(self.stdscr, row, list_w, curses.ACS_VLINE, attr)

    def draw_list(self, sh: int, list_w: int) -> None:
        visible = sh - 2

        if self.cursor < self.offset:
            self.offset = self.cursor
        elif self.cursor >= self.offset + visible:
            self.offset = self.cursor - visible + 1

        for i in range(visible):
            idx = self.offset + i
            row = i + 1

            if idx >= len(self.filtered):
                safe_addstr(self.stdscr, row, 0,
                            " " * list_w, curses.color_pair(C_NORMAL))
                continue

            movie  = self.filtered[idx]
            is_sel = idx == self.cursor
            title  = movie["title"]

            # Prefix layout (all ASCII, each char = 1 terminal column):
            #   col 0 : space
            #   col 1 : video mark  (> or space)
            #   col 2 : nfo mark    (* or space)
            #   col 3 : space
            #   col 4+ : title
            vmark = _MARK_VIDEO if movie["has_video"] else _MARK_EMPTY
            nmark = _MARK_NFO   if movie["has_nfo"]   else " "
            prefix = f" {vmark}{nmark} "   # 4 chars, 4 columns — guaranteed
            avail  = list_w - len(prefix)
            row_text = prefix + title[:max(0, avail)]
            # Right-pad to list_w
            row_text = row_text + " " * (list_w - len(row_text))
            row_text = row_text[:list_w]

            if is_sel:
                safe_addstr(self.stdscr, row, 0, row_text,
                            curses.color_pair(C_SELECTED) | curses.A_BOLD)
            else:
                # Base row in normal colour
                safe_addstr(self.stdscr, row, 0, row_text,
                            curses.color_pair(C_NORMAL))
                # Colour marks individually
                if movie["has_video"]:
                    safe_addstr(self.stdscr, row, 1, vmark,
                                curses.color_pair(C_ACCENT) | curses.A_BOLD)
                else:
                    safe_addstr(self.stdscr, row, 1, vmark,
                                curses.color_pair(C_WARN))
                if movie["has_nfo"]:
                    safe_addstr(self.stdscr, row, 2, nmark,
                                curses.color_pair(C_DIM))

    def draw_info_panel(self, sh: int, sw: int, list_w: int, info_w: int) -> None:
        if info_w < 10:
            return
        panel = self.stdscr.subwin(sh - 2, info_w, 1, list_w + 1)

        if not self.filtered:
            panel.erase()
            safe_addstr(panel, 2, 2, "[ NO SIGNAL ]",
                        curses.color_pair(C_WARN) | curses.A_BOLD)
            panel.noutrefresh()
            return

        movie = self.filtered[self.cursor]
        info  = self.get_info(movie)
        render_info(panel, movie, info)

        btn_row = sh - 4
        if btn_row > 1 and movie["has_video"]:
            safe_addstr(panel, btn_row, 2, "  >> PLAY FILM <<  ",
                        curses.color_pair(C_PLAY_BTN) | curses.A_BOLD)

    def draw_search_bar(self, sh: int, list_w: int) -> None:
        if not self.search_mode:
            return
        row = sh - 2
        query_disp = f"  SCAN: {self.search}_"
        text = query_disp + " " * max(0, list_w - len(query_disp))
        safe_addstr(self.stdscr, row, 0, text[:list_w],
                    curses.color_pair(C_SEARCH) | curses.A_BOLD)

    def redraw(self) -> None:
        sh, sw, list_w, info_w = self.dimensions()
        self.stdscr.erase()
        self.draw_title_bar(sh, sw)
        self.draw_status_bar(sh, sw)
        self.draw_divider(sh, sw, list_w)
        self.draw_list(sh, list_w)
        self.draw_info_panel(sh, sw, list_w, info_w)
        self.draw_search_bar(sh, list_w)
        curses.doupdate()

    # ── Input ──────────────────────────────────────────────────────────────────

    def handle_search_key(self, key: int) -> None:
        if key == 27:
            self.search_mode = False
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            self.search = self.search[:-1]
            self.apply_filter()
        elif 32 <= key <= 126:
            self.search += chr(key)
            self.apply_filter()
        elif key in (curses.KEY_ENTER, 10, 13):
            self.search_mode = False

    def handle_normal_key(self, key: int) -> str:
        n = len(self.filtered)

        # ── Accumulate numeric prefix (e.g. "10j" → move 10 down) ──
        if 48 <= key <= 57:               # 0-9
            self.count_buf = self.count_buf * 10 + (key - 48)
            return ""

        count = max(1, self.count_buf)
        self.count_buf = 0                # consume prefix

        def move(delta: int) -> None:
            prev = self.cursor
            self.cursor = clamp(self.cursor + delta, 0, max(0, n - 1))
            if self.cursor != prev:
                play_click()

        if key in (ord("q"), ord("Q")):
            return "quit"

        # ── Motion keys ──
        elif key in (curses.KEY_UP,   ord("k")):  move(-count)
        elif key in (curses.KEY_DOWN, ord("j")):  move( count)
        elif key in (curses.KEY_LEFT, ord("h")):  move(-count * 10)
        elif key in (curses.KEY_RIGHT,ord("l")):  move( count * 10)

        # Ctrl-U / Ctrl-D  (half page)
        elif key == 21:                           # Ctrl-U
            sh, *_ = self.dimensions()
            move(-(sh // 2) * count)
        elif key == 4:                            # Ctrl-D
            sh, *_ = self.dimensions()
            move( (sh // 2) * count)

        # Ctrl-B / Ctrl-F  (full page)
        elif key in (curses.KEY_PPAGE, 2):        # PgUp / Ctrl-B
            sh, *_ = self.dimensions()
            move(-(sh - 2) * count)
        elif key in (curses.KEY_NPAGE, 6):        # PgDn / Ctrl-F
            sh, *_ = self.dimensions()
            move( (sh - 2) * count)

        # gg / G
        elif key == ord("g"):
            if self._last_key == ord("g"):        # gg → top
                self.cursor = 0
                play_click()
            # else: wait for second g
        elif key == ord("G"):
            if count > 1:                         # 42G → line 42
                self.cursor = clamp(count - 1, 0, max(0, n - 1))
            else:
                self.cursor = max(0, n - 1)       # G  → bottom
            play_click()

        # ── Actions ──
        elif key in (curses.KEY_ENTER, 10, 13, ord("p")):
            return "play"
        elif key in (ord("/"), ord("f")):
            self.search_mode = True

        self._last_key = key
        return ""

    # ── Main loop ──────────────────────────────────────────────────────────────

    def run(self) -> None:
        self.setup()
        while True:
            self.redraw()
            key = self.stdscr.getch()

            if self.search_mode:
                self.handle_search_key(key)
                continue

            action = self.handle_normal_key(key)

            if action == "quit":
                stop_click_server()
                break

            if action == "play":
                if not self.filtered:
                    continue
                movie = self.filtered[self.cursor]
                if not movie["has_video"]:
                    continue
                if confirm_play(self.stdscr, movie):
                    curses.endwin()
                    play_movie(movie["folder"])
                    self.stdscr = curses.initscr()
                    init_colors()
                    curses.curs_set(0)
                    self.stdscr.keypad(True)


# ─── ENTRY ────────────────────────────────────────────────────────────────────

def run() -> None:
    curses.wrapper(lambda stdscr: MovieOdysseyApp(stdscr).run())
