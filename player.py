"""
player.py — Launch mpv with idle inhibition.
"""

import os
import sys
import shutil
import termios

from library import find_video


# ─── STDIN FLUSH ──────────────────────────────────────────────────────────────

def flush_stdin():
    """Discard buffered keypresses left over from mpv (e.g. the 'q' that quit it)."""
    try:
        termios.tcflush(sys.stdin, termios.TCIFLUSH)
    except Exception:
        pass  # Non-TTY — safe to ignore


# ─── PLAY ─────────────────────────────────────────────────────────────────────

def play_movie(folder: str) -> None:
    video = find_video(folder)
    if not video:
        print("\n  [!] No video file found in that folder.")
        return

    if shutil.which("gnome-session-inhibit"):
        os.system(
            f'gnome-session-inhibit --inhibit idle '
            f'--reason "Watching a film" mpv "{video}"'
        )
    elif shutil.which("systemd-inhibit"):
        os.system(
            f'systemd-inhibit --what=idle --who="Movie Odyssey" '
            f'--why="Watching a film" mpv "{video}"'
        )
    else:
        os.system(f'mpv "{video}"')

    flush_stdin()
