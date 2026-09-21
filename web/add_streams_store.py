# This file is a part of NEO-WZML (github.com/IbrahimKhan2004/NEO-WZML)

import json
import os
from contextlib import suppress
from functools import lru_cache
from re import sub
from typing import Optional

from pycountry import languages

_BASE_DIR = os.path.join(os.getcwd(), "downloads", ".add_streams")
# Same list as bot.helper.ext_utils.merge_utils.VIDEO_EXTS (the web server
# process must not import the bot package).
_VIDEO_EXTS = (".mp4", ".mkv", ".avi", ".mov", ".webm", ".ts", ".m2ts")


def _path(gid: str) -> str:
    return os.path.join(_BASE_DIR, f"{gid}.json")


def _valid_gid(gid: str) -> bool:
    return bool(gid) and all(c.isalnum() or c in "-_" for c in gid)


@lru_cache(maxsize=1)
def get_languages() -> list:
    langs = {
        lang.alpha_3: sub(r"\s*\(.*\)$", "", lang.name)
        for lang in languages
        if hasattr(lang, "alpha_2")
    }
    langs.setdefault("bih", "Bihari")
    ordered = sorted(langs.items(), key=lambda kv: kv[1].lower())
    return [["und", "Undetermined"], *[[code, name] for code, name in ordered]]


def normalize_language(code) -> str:
    """Map any 2/3 letter language code (incl. ISO 639-2/B) to a listed 3 letter code."""
    code = str(code or "").strip().lower()
    valid = {c for c, _ in get_languages()}
    if code in valid:
        return code
    if len(code) in (2, 3):
        with suppress(Exception):
            lang = (
                languages.get(alpha_2=code)
                if len(code) == 2
                else languages.get(bibliographic=code)
            )
            if lang and lang.alpha_3 in valid:
                return lang.alpha_3
    return "und"


def resolve_output_name(base_path: str, output_name: str = "") -> str:
    """Final file name of a muxed group: custom name (or the original name) + .mkv"""
    name = (output_name or "").strip() or os.path.basename(base_path)
    if name.lower().endswith(_VIDEO_EXTS):
        name = os.path.splitext(name)[0]
    return f"{name}.mkv"


def write_state(gid: str, data: dict) -> bool:
    """
    data: {"videos": [{"path", "size"}],
           "audios": [{"path", "size", "streams": [{"index", "language", "title"}]}],
           "subtitles": [same shape as audios]}
    """
    if not _valid_gid(gid):
        return False
    try:
        os.makedirs(_BASE_DIR, exist_ok=True)
        with open(_path(gid), "w", encoding="utf-8") as f:
            json.dump({**data, "groups": []}, f)
        return True
    except OSError:
        return False


def read_state(gid: str) -> Optional[dict]:
    if not _valid_gid(gid):
        return None
    try:
        with open(_path(gid), encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def save_groups(gid: str, groups: list) -> bool:
    state = read_state(gid)
    if state is None:
        return False
    state["groups"] = groups
    try:
        with open(_path(gid), "w", encoding="utf-8") as f:
            json.dump(state, f)
        return True
    except OSError:
        return False


def get_groups(gid: str) -> list:
    state = read_state(gid) or {}
    groups = state.get("groups", [])
    return groups if isinstance(groups, list) else []


def delete_state(gid: str) -> None:
    try:
        os.remove(_path(gid))
    except OSError:
        pass


def get_add_data(gid: str) -> Optional[dict]:
    state = read_state(gid)
    if state is None:
        return None
    out = {"languages": get_languages()}
    for key in ("videos", "audios", "subtitles", "groups"):
        val = state.get(key, [])
        out[key] = val if isinstance(val, list) else []
    return out


def clean_groups(data: dict, groups) -> tuple:
    """Validate submitted groups against the state. Returns (groups, error)."""
    if not isinstance(groups, list) or not groups:
        return None, "Add at least one group."
    videos = {v.get("path") for v in data["videos"] if isinstance(v, dict)}
    externals = {
        "audio": {
            f.get("path"): len(f.get("streams") or [])
            for f in data["audios"]
            if isinstance(f, dict)
        },
        "subtitle": {
            f.get("path"): len(f.get("streams") or [])
            for f in data["subtitles"]
            if isinstance(f, dict)
        },
    }
    used_videos = set()
    used_outputs = set()
    valid = []
    for group in groups:
        if not isinstance(group, dict):
            return None, "Invalid group."
        base = group.get("base_video")
        if base not in videos or base in used_videos:
            return None, "Invalid or duplicate base video."
        used_videos.add(base)
        name = str(group.get("output_name") or "").strip()
        if (
            name != os.path.basename(name.replace("\\", "/"))
            or name in (".", "..")
            or "\x00" in name
            or "\n" in name
            or "\r" in name
            or len(name) > 200
        ):
            return None, "Invalid output file name."
        out_key = (os.path.dirname(base), resolve_output_name(base, name).lower())
        if out_key in used_outputs:
            return None, "Two groups have the same output file name."
        used_outputs.add(out_key)
        tracks = group.get("tracks")
        if not isinstance(tracks, list) or not tracks:
            return None, "Every group needs at least one audio/subtitle track."
        clean_tracks = []
        defaults = set()
        for track in tracks:
            if not isinstance(track, dict):
                return None, "Invalid track."
            ttype = track.get("type")
            file_ = track.get("file")
            index = track.get("index")
            if (
                ttype not in externals
                or file_ not in externals[ttype]
                or not isinstance(index, int)
                or isinstance(index, bool)
                or not 0 <= index < externals[ttype][file_]
            ):
                return None, "Invalid track selection."
            is_default = track.get("default") is True
            if is_default:
                if ttype in defaults:
                    return None, f"Only one default {ttype} track is allowed per group."
                defaults.add(ttype)
            clean_tracks.append(
                {
                    "type": ttype,
                    "file": file_,
                    "index": index,
                    "language": normalize_language(track.get("language")),
                    "title": str(track.get("title") or "").strip()[:255],
                    "default": is_default,
                }
            )
        valid.append({"base_video": base, "output_name": name, "tracks": clean_tracks})
    return valid, ""
