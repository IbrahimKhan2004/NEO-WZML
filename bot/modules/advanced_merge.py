# This file is a part of NEO-WZML (github.com/irisXDR/NEO-WZML)

from asyncio import Event, wait_for
from os import path as ospath, walk
from secrets import token_hex

from aiofiles.os import path as aiopath
from pyrogram.filters import regex
from pyrogram.handlers import CallbackQueryHandler

from bot.core.config_manager import Config
from bot.core.tg_client import TgClient
from bot.helper.ext_utils.merge_utils import VIDEO_EXTS
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.telegram_helper.message_utils import delete_message, send_message
from web.advanced_merge_store import delete_state, get_groups, write_state

_pending = {}


async def get_advanced_merge_config(listener, dl_path):
    files = []
    base = dl_path if await aiopath.isdir(dl_path) else ospath.dirname(dl_path)
    parent_dir = ospath.dirname(dl_path)
    for root, _, names in walk(base):
        for name in names:
            path = ospath.join(root, name)
            if name.lower().endswith(VIDEO_EXTS) and await aiopath.isfile(path):
                files.append({"path": ospath.relpath(path, parent_dir), "size": ospath.getsize(path)})
    from natsort import natsorted

    files = natsorted(files, key=lambda f: f["path"])
    if not files:
        await listener.on_upload_error("No video files found for Advanced Video Merge!")
        return None
    if not Config.BASE_URL:
        await listener.on_upload_error("BASE_URL is required for Advanced Video Merge.")
        return None
    gid = token_hex(12)
    if not write_state(gid, files):
        await listener.on_upload_error("Unable to prepare Advanced Video Merge.")
        return None
    done = Event()
    _pending[gid] = (listener.user_id, done)
    buttons = ButtonMaker()
    base_url = (Config.BASE_URL or "").rstrip("/")
    buttons.url_button("Open Web UI", f"{base_url}/app/merge?gid={gid}")
    buttons.data_button("Done", f"am done {gid}")
    msg = await send_message(
        listener.message,
        f"{listener.tag},\n\n<b>Advanced Video Merge Pending</b>\n\n"
        "Your files have finished downloading. Please click the button below to "
        "open the Web UI and configure your settings.\n\n"
        "I will wait up to 15 minutes for your submission.",
        buttons.build_menu(1),
    )
    from bot import task_dict, task_dict_lock
    from bot.helper.mirror_leech_utils.status_utils.merge_status import AdvancedMergeStatus

    async with task_dict_lock:
        task_dict[listener.mid] = AdvancedMergeStatus(listener, gid)

    try:
        await wait_for(done.wait(), timeout=900)
    except TimeoutError:
        await listener.on_upload_error("Advanced Video Merge configuration timed out.")
        delete_state(gid)
        return None
    finally:
        _pending.pop(gid, None)
        async with task_dict_lock:
            task_dict.pop(listener.mid, None)
        await delete_message(msg)
    groups = get_groups(gid)
    delete_state(gid)
    return base, groups


async def advanced_merge_done(_, query):
    _, action, gid = query.data.split()
    pending = _pending.get(gid)
    if action != "done" or not pending:
        return await query.answer("This merge request has expired.", show_alert=True)
    user_id, done = pending
    if query.from_user.id != user_id:
        return await query.answer("Not Yours!", show_alert=True)
    if not get_groups(gid):
        return await query.answer("Save a non-empty merge group in the Web UI first.", show_alert=True)
    done.set()
    await query.answer("Advanced merge started!")


TgClient.bot.add_handler(CallbackQueryHandler(advanced_merge_done, filters=regex("^am done")))
