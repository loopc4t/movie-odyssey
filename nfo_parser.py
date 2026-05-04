"""
nfo_parser.py — Parse TinyMediaManager .nfo (Kodi-format XML) files.
"""

import xml.etree.ElementTree as ET
from typing import Any


def _text(root: ET.Element, tag: str, fallback: str = "") -> str:
    el = root.find(tag)
    return (el.text or "").strip() if el is not None else fallback


def _texts(root: ET.Element, tag: str) -> list[str]:
    return [
        (el.text or "").strip()
        for el in root.findall(tag)
        if (el.text or "").strip()
    ]


def parse_nfo(path: str) -> dict[str, Any]:
    """
    Parse a TinyMediaManager .nfo file and return a clean info dict.

    Returns an empty dict on any parse error.
    """
    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except Exception:
        return {}

    # Ratings — TMM may use <ratings><rating name="imdb"><value>…
    rating = ""
    ratings_el = root.find("ratings")
    if ratings_el is not None:
        for r in ratings_el.findall("rating"):
            val = r.find("value")
            if val is not None and val.text:
                name = r.get("name", "")
                rating = f"{float(val.text):.1f}"
                if name:
                    rating += f"  ({name.upper()})"
                break
    if not rating:
        rating = _text(root, "rating")

    # Actors
    actors = []
    for actor_el in root.findall("actor"):
        name = _text(actor_el, "name")
        role = _text(actor_el, "role")
        if name:
            actors.append({"name": name, "role": role})

    # Director(s) — TMM writes multiple <director> tags
    directors = _texts(root, "director")

    # Writers
    writers = _texts(root, "credits")

    # Genres
    genres = _texts(root, "genre")

    # Studios
    studios = _texts(root, "studio")

    # Countries
    countries = _texts(root, "country")

    # Tags / keywords
    tags = _texts(root, "tag")

    # Runtime (minutes)
    runtime = _text(root, "runtime")

    # fileinfo → video / audio streams
    file_info: dict[str, Any] = {}
    fi_el = root.find("fileinfo")
    if fi_el is not None:
        si_el = fi_el.find("streamdetails")
        if si_el is not None:
            vid_el = si_el.find("video")
            aud_el = si_el.find("audio")
            if vid_el is not None:
                file_info["video"] = {
                    "codec": _text(vid_el, "codec"),
                    "width": _text(vid_el, "width"),
                    "height": _text(vid_el, "height"),
                    "aspect": _text(vid_el, "aspect"),
                }
            if aud_el is not None:
                file_info["audio"] = {
                    "codec": _text(aud_el, "codec"),
                    "channels": _text(aud_el, "channels"),
                    "language": _text(aud_el, "language"),
                }

    return {
        "title": _text(root, "title"),
        "original_title": _text(root, "originaltitle"),
        "sort_title": _text(root, "sorttitle"),
        "year": _text(root, "year"),
        "rating": rating,
        "votes": _text(root, "votes"),
        "mpaa": _text(root, "mpaa"),
        "runtime": runtime,
        "tagline": _text(root, "tagline"),
        "plot": _text(root, "plot"),
        "outline": _text(root, "outline"),
        "genres": genres,
        "tags": tags,
        "directors": directors,
        "writers": writers,
        "actors": actors,
        "studios": studios,
        "countries": countries,
        "file_info": file_info,
        "imdb_id": _text(root, "imdbid") or _text(root, "id"),
        "tmdb_id": _text(root, "tmdbid"),
        "premiered": _text(root, "premiered") or _text(root, "releasedate"),
        "watched": _text(root, "watched"),
        "playcount": _text(root, "playcount"),
    }
