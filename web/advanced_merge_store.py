# This file is a part of NEO-WZML (github.com/irisXDR/NEO-WZML)

import json
import os
from typing import Optional

_BASE_DIR = "/usr/src/app/downloads/.advanced_merge"


def _path(gid: str) -> str:
    return os.path.join(_BASE_DIR, f"{gid}.json")


def _valid_gid(gid: str) -> bool:
    return bool(gid) and all(c.isalnum() or c in "-_" for c in gid)


def write_state(gid: str, files: list) -> bool:
    if not _valid_gid(gid):
        return False
    try:
        os.makedirs(_BASE_DIR, exist_ok=True)
        with open(_path(gid), "w", encoding="utf-8") as f:
            json.dump({"files": files, "groups": []}, f)
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


def get_file_list(gid: str) -> Optional[list]:
    state = read_state(gid)
    files = state.get("files") if state else None
    return files if isinstance(files, list) else None
