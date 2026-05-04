"""
library.py — Scan the Movies directory and locate video files.
"""

import os

MOVIES_DIR = os.path.expanduser("~/Videos/Movies")

VIDEO_EXTENSIONS = {
    ".mp4", ".mkv", ".avi", ".mov", ".m4v",
    ".wmv", ".flv", ".webm", ".ts", ".mpg", ".mpeg",
}


def find_video(folder: str) -> str | None:
    """Return the first video file found inside *folder*, or None."""
    try:
        for entry in sorted(os.scandir(folder), key=lambda e: e.name):
            if entry.is_file():
                _, ext = os.path.splitext(entry.name)
                if ext.lower() in VIDEO_EXTENSIONS:
                    return entry.path
    except PermissionError:
        pass
    return None


def find_nfo(folder: str) -> str | None:
    """Return the first .nfo file found inside *folder*, or None."""
    try:
        for entry in sorted(os.scandir(folder), key=lambda e: e.name):
            if entry.is_file() and entry.name.lower().endswith(".nfo"):
                return entry.path
    except PermissionError:
        pass
    return None


def find_poster(folder: str) -> str | None:
    """Return a poster image path if one exists."""
    candidates = ("poster", "-poster", "_poster", "folder", "cover")
    image_exts = {".jpg", ".jpeg", ".png", ".webp"}
    try:
        for entry in sorted(os.scandir(folder), key=lambda e: e.name):
            if entry.is_file():
                name_lower = entry.name.lower()
                _, ext = os.path.splitext(name_lower)
                if ext in image_exts:
                    stem = name_lower[: len(name_lower) - len(ext)]
                    if any(stem.endswith(c) for c in candidates):
                        return entry.path
    except PermissionError:
        pass
    return None


def scan_movies(movies_dir: str = MOVIES_DIR) -> list[dict]:
    """
    Walk movies_dir and return a list of movie dicts, sorted by title.

    Each dict has keys:
      title        str   — folder name (fallback display title)
      folder       str   — absolute path to the movie folder
      has_video    bool
      has_nfo      bool
      nfo_path     str | None
      video_path   str | None
      poster_path  str | None
    """
    movies = []
    if not os.path.isdir(movies_dir):
        return movies

    with os.scandir(movies_dir) as top:
        for entry in top:
            if not entry.is_dir():
                continue
            folder = entry.path
            title = entry.name
            video = find_video(folder)
            nfo = find_nfo(folder)
            poster = find_poster(folder)
            movies.append(
                {
                    "title": title,
                    "folder": folder,
                    "has_video": video is not None,
                    "has_nfo": nfo is not None,
                    "video_path": video,
                    "nfo_path": nfo,
                    "poster_path": poster,
                }
            )

    movies.sort(key=lambda m: m["title"].lower())
    return movies
