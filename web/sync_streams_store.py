# This file is a part of NEO-WZML (github.com/IbrahimKhan2004/NEO-WZML)

import json
import os
from typing import Optional

_BASE_DIR = os.path.join(os.getcwd(), "downloads", ".sync_streams")


def _path(gid: str) -> str:
    return os.path.join(_BASE_DIR, f"{gid}.json")


def _valid_gid(gid: str) -> bool:
    return bool(gid) and all(c.isalnum() or c in "-_" for c in gid)


def write_state(gid: str, files: list) -> bool:
    """
    files: list of dicts, e.g.:
    [
      {
        "path": "video1.mkv",
        "tracks": [
           {"id": 1, "type": "audio", "title": "Hindi", "language": "Hindi", "codec": "mp3", "delay": 0},
           {"id": 2, "type": "subtitle", "title": "English", "language": "English", "codec": "subrip", "delay": 0}
        ]
      }
    ]
    """
    if not _valid_gid(gid):
        return False
    try:
        os.makedirs(_BASE_DIR, exist_ok=True)
        with open(_path(gid), "w", encoding="utf-8") as f:
            json.dump({"files": files, "delays": {}, "submitted": False}, f)
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


def save_delays(gid: str, delays: dict) -> bool:
    """
    delays mapping file path to track_id -> delay_ms dict, e.g.:
    {
      "video1.mkv": {
        "1": 500,
        "2": -200
      }
    }
    """
    state = read_state(gid)
    if state is None:
        return False
    state["delays"] = delays
    state["submitted"] = True
    try:
        with open(_path(gid), "w", encoding="utf-8") as f:
            json.dump(state, f)
        return True
    except OSError:
        return False


def get_delays(gid: str) -> Optional[dict]:
    state = read_state(gid)
    if state is None or not state.get("submitted"):
        return None
    return state.get("delays", {})


def delete_state(gid: str) -> None:
    try:
        os.remove(_path(gid))
    except OSError:
        pass


def get_sync_data(gid: str) -> Optional[dict]:
    state = read_state(gid)
    if state is None:
        return None
    return {
        "files": state.get("files", []),
        "delays": state.get("delays", {}),
        "submitted": state.get("submitted", False),
    }
