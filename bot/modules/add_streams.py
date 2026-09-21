# This file is a part of NEO-WZML (github.com/IbrahimKhan2004/NEO-WZML)

from asyncio import Event, wait_for
from os import path as ospath, walk
from secrets import token_hex

from aiofiles.os import path as aiopath
from natsort import natsorted
from pyrogram.filters import regex
from pyrogram.handlers import CallbackQueryHandler

from bot.core.config_manager import Config
from bot.core.tg_client import TgClient
from bot.helper.ext_utils.media_utils import get_streams
from bot.helper.ext_utils.merge_utils import VIDEO_EXTS
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.telegram_helper.message_utils import delete_message, send_message
from web.add_streams_store import (
    delete_state,
    get_groups,
    normalize_language,
    write_state,
)

AUDIO_EXTS = (
    ".aac", ".m4a", ".mp3", ".ac3", ".eac3", ".ec3", ".dts",
    ".flac", ".opus", ".ogg", ".oga", ".wav", ".mka",
)
SUBTITLE_EXTS = (".srt", ".ass", ".ssa", ".vtt", ".sub", ".sup", ".mks")

_pending = {}


async def _external_entry(path, parent_dir, codec_type):
    streams = [
        s for s in (await get_streams(path) or []) if s.get("codec_type") == codec_type
    ]
    if not streams:
        return None
    return {
        "path": ospath.relpath(path, parent_dir),
        "size": ospath.getsize(path),
        "streams": [
            {
                "index": i,
                "language": normalize_language((s.get("tags") or {}).get("language")),
                "title": (s.get("tags") or {}).get("title") or "",
            }
            for i, s in enumerate(streams)
        ],
    }


async def get_add_streams_config(listener, dl_path):
    if await aiopath.isfile(dl_path):
        await listener.on_upload_error(
            "Add Audio/Subtitles needs a video plus audio/subtitle files in one "
            "folder! Use -i <count> -m <folder> -vt."
        )
        return None
    parent_dir = ospath.dirname(dl_path)
    videos, audios, subtitles = [], [], []
    for root, _, names in walk(dl_path):
        for name in names:
            path = ospath.join(root, name)
            low = name.lower()
            if not await aiopath.isfile(path):
                continue
            if low.endswith(VIDEO_EXTS):
                videos.append(path)
            elif low.endswith(AUDIO_EXTS):
                audios.append(path)
            elif low.endswith(SUBTITLE_EXTS):
                subtitles.append(path)
    if not videos:
        await listener.on_upload_error("No video files found for Add Audio/Subtitles!")
        return None
    audio_files = [
        e
        for e in [
            await _external_entry(p, parent_dir, "audio") for p in natsorted(audios)
        ]
        if e
    ]
    subtitle_files = [
        e
        for e in [
            await _external_entry(p, parent_dir, "subtitle")
            for p in natsorted(subtitles)
        ]
        if e
    ]
    if not audio_files and not subtitle_files:
        await listener.on_upload_error(
            "No external audio/subtitle files found to add!"
        )
        return None
    if not Config.BASE_URL:
        await listener.on_upload_error("BASE_URL is required for Add Audio/Subtitles.")
        return None
    gid = token_hex(12)
    state = {
        "videos": [
            {"path": ospath.relpath(p, parent_dir), "size": ospath.getsize(p)}
            for p in natsorted(videos)
        ],
        "audios": audio_files,
        "subtitles": subtitle_files,
    }
    if not write_state(gid, state):
        await listener.on_upload_error("Unable to prepare Add Audio/Subtitles.")
        return None
    done = Event()
    _pending[gid] = (listener.user_id, done)
    buttons = ButtonMaker()
    base_url = (Config.BASE_URL or "").rstrip("/")
    buttons.url_button("Open Web UI", f"{base_url}/app/add_streams?gid={gid}")
    buttons.data_button("Done", f"addst done {gid}")
    msg = await send_message(
        listener.message,
        f"{listener.tag},\n\n<b>Add Audio/Subtitles Pending</b>\n\n"
        "Your files have finished downloading. Please click the button below to "
        "open the Web UI and configure your settings.\n\n"
        "I will wait up to 15 minutes for your submission.",
        buttons.build_menu(1),
    )
    from bot import task_dict, task_dict_lock
    from bot.helper.mirror_leech_utils.status_utils.merge_status import (
        AddStreamsStatus,
    )

    async with task_dict_lock:
        task_dict[listener.mid] = AddStreamsStatus(listener, gid)

    try:
        await wait_for(done.wait(), timeout=900)
    except TimeoutError:
        await listener.on_upload_error("Add Audio/Subtitles configuration timed out.")
        delete_state(gid)
        return None
    finally:
        _pending.pop(gid, None)
        async with task_dict_lock:
            task_dict.pop(listener.mid, None)
        await delete_message(msg)
    if listener.is_cancelled:
        return None
    groups = get_groups(gid)
    delete_state(gid)
    return groups


async def add_streams_done(_, query):
    _, action, gid = query.data.split()
    pending = _pending.get(gid)
    if action != "done" or not pending:
        return await query.answer("This request has expired.", show_alert=True)
    user_id, done = pending
    if query.from_user.id != user_id:
        return await query.answer("Not Yours!", show_alert=True)
    if not get_groups(gid):
        return await query.answer(
            "Save a valid configuration in the Web UI first.", show_alert=True
        )
    done.set()
    await query.answer("Add Audio/Subtitles started!")


TgClient.bot.add_handler(
    CallbackQueryHandler(add_streams_done, filters=regex("^addst done"))
)
