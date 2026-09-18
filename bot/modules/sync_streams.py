# This file is a part of NEO-WZML (github.com/IbrahimKhan2004/NEO-WZML)

from asyncio import Event, wait_for
from os import path as ospath, walk
from secrets import token_hex
from contextlib import suppress

from aiofiles.os import path as aiopath
from natsort import natsorted
from langcodes import Language
from pyrogram.filters import regex
from pyrogram.handlers import CallbackQueryHandler

from bot.core.config_manager import Config
from bot.core.tg_client import TgClient
from bot.helper.ext_utils.media_utils import get_streams
from bot.helper.ext_utils.merge_utils import VIDEO_EXTS
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.telegram_helper.message_utils import delete_message, send_message
from web.sync_streams_store import delete_state, get_delays, write_state

_pending = {}


async def get_sync_streams_config(listener, dl_path):
    files = []
    base = dl_path if await aiopath.isdir(dl_path) else ospath.dirname(dl_path)
    parent_dir = ospath.dirname(dl_path)

    if await aiopath.isfile(dl_path):
        if dl_path.lower().endswith(VIDEO_EXTS):
            files_to_check = [dl_path]
        else:
            files_to_check = []
    else:
        files_to_check = []
        for root, _, names in walk(base):
            for name in names:
                path = ospath.join(root, name)
                if name.lower().endswith(VIDEO_EXTS) and await aiopath.isfile(path):
                    files_to_check.append(path)

    files_to_check = natsorted(files_to_check)
    if not files_to_check:
        await listener.on_upload_error("No video files found for Sync Audio/Subtitles!")
        return None

    files_data = []
    for file_path in files_to_check:
        rel_path = ospath.relpath(file_path, parent_dir)
        streams = await get_streams(file_path) or []
        tracks = []
        for s in streams:
            codec_type = s.get("codec_type")
            if codec_type in ["audio", "subtitle"]:
                track_id = s.get("index")
                codec_name = s.get("codec_name", "")
                tags = s.get("tags") or {}
                title = tags.get("title") or ""
                lang_code = tags.get("language") or ""
                lang_name = ""
                if lang_code:
                    with suppress(Exception):
                        lang_name = Language.get(lang_code).display_name()
                label = title or lang_name or lang_code or f"Track {track_id}"
                tracks.append({
                    "id": track_id,
                    "type": codec_type,
                    "title": label,
                    "language": lang_name or lang_code,
                    "codec": codec_name,
                    "delay": 0
                })
        if tracks:
            files_data.append({
                "path": rel_path,
                "tracks": tracks
            })

    if not files_data:
        await listener.on_upload_error("No audio or subtitle streams found to sync!")
        return None

    if not Config.BASE_URL:
        await listener.on_upload_error("BASE_URL is required for Sync Audio/Subtitles.")
        return None

    gid = token_hex(12)
    if not write_state(gid, files_data):
        await listener.on_upload_error("Unable to prepare Sync Audio/Subtitles configuration.")
        return None

    done = Event()
    _pending[gid] = (listener.user_id, done)

    buttons = ButtonMaker()
    base_url = (Config.BASE_URL or "").rstrip("/")
    buttons.url_button("Open Web UI", f"{base_url}/app/sync_streams?gid={gid}")
    buttons.data_button("Done", f"sync done {gid}")

    msg = await send_message(
        listener.message,
        f"{listener.tag},\n\n<b>Sync Audio/Subtitles Pending</b>\n\n"
        "Your files have finished downloading. Please click the button below to "
        "open the Web UI and configure your settings.\n"
        "I will wait up to 15 minutes for your submission.",
        buttons.build_menu(1),
    )

    from bot import task_dict, task_dict_lock
    from bot.helper.mirror_leech_utils.status_utils.merge_status import SyncStreamsStatus

    async with task_dict_lock:
        task_dict[listener.mid] = SyncStreamsStatus(listener, gid)

    try:
        await wait_for(done.wait(), timeout=900)
    except TimeoutError:
        await listener.on_upload_error("Sync Audio/Subtitles configuration timed out.")
        delete_state(gid)
        return None
    finally:
        _pending.pop(gid, None)
        async with task_dict_lock:
            task_dict.pop(listener.mid, None)
        await delete_message(msg)

    if listener.is_cancelled:
        return None

    delays = get_delays(gid)
    delete_state(gid)
    return delays


async def sync_streams_done(_, query):
    _, action, gid = query.data.split()
    pending = _pending.get(gid)
    if action != "done" or not pending:
        return await query.answer("This sync request has expired.", show_alert=True)
    user_id, done = pending
    if query.from_user.id != user_id:
        return await query.answer("Not Yours!", show_alert=True)
    done.set()
    await query.answer("Sync stream processing started!")


TgClient.bot.add_handler(CallbackQueryHandler(sync_streams_done, filters=regex("^sync done")))
