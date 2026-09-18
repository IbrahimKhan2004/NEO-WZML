# This file is a part of NEO-WZML (github.com/IbrahimKhan2004/NEO-WZML)

from asyncio import sleep
from contextlib import suppress
from time import time

from bot.helper.ext_utils.bot_utils import new_task
from bot.helper.ext_utils.media_utils import get_streams
from bot.helper.ext_utils.metadata_utils import MetadataProcessor
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.telegram_helper.message_utils import delete_message, edit_message, send_message

RS_TIMEOUT = 15 * 60
rs_dict = {}


def _group_label(ctype, lang):
    if ctype == "video":
        return "Video"
    if lang in (None, "und", "unknown", "none", ""):
        lang_name = "unknown"
    else:
        lang_name = MetadataProcessor.convert_lang_code(lang)
    return f"{ctype.capitalize()} - {lang_name}"


def _rs_text(tag, rstate, time_left):
    count = len(rstate["selected"])
    status_line = (
        "No streams selected yet."
        if count == 0
        else f"{count} stream(s) selected for removal."
    )
    return (
        f"<b>Remove Stream for</b> {tag}\n\n"
        "<b>Select the stream(s) you want to remove!</b>\n"
        f"<b>Timeout:</b> {round(time_left // 60)} Min\n\n"
        f"{status_line}\n\n"
        "<b>Note:</b> Attachments are removed by default. Click Done to proceed."
    )


def _rs_menu(rstate):
    buttons = ButtonMaker()
    for idx, (ctype, lang, _) in enumerate(rstate["groups"]):
        tick = "✅ " if idx in rstate["selected"] else ""
        buttons.data_button(f"{tick}{_group_label(ctype, lang)}", f"rss tgl {idx}")
    buttons.data_button("🎵 All Audio", "rss allaudio", "f_body")
    buttons.data_button("📜 All Subtitles", "rss allsub", "f_body")
    buttons.data_button("🔄 Reverse Selection", "rss rev", "l_body")
    buttons.data_button("Done", "rss done", "footer")
    buttons.data_button("❌ Close", "rss close", "footer")
    return buttons.build_menu(2, fb_cols=2, lb_cols=1, f_cols=2)


@new_task
async def edit_remove_stream_selection(client, query):
    message = query.message
    mid = message.id
    rstate = rs_dict.get(mid)
    if not rstate:
        return await query.answer()
    if query.from_user.id != rstate["user_id"]:
        return await query.answer("Not Yours!", show_alert=True)

    parts = query.data.split()
    action = parts[1]

    if action == "tgl":
        idx = int(parts[2])
        rstate["selected"].symmetric_difference_update({idx})
        await query.answer()
    elif action == "allaudio":
        audio_idxs = {
            i for i, (ctype, _, _) in enumerate(rstate["groups"]) if ctype == "audio"
        }
        if audio_idxs and audio_idxs.issubset(rstate["selected"]):
            rstate["selected"] -= audio_idxs
        else:
            rstate["selected"] |= audio_idxs
        await query.answer()
    elif action == "allsub":
        sub_idxs = {
            i
            for i, (ctype, _, _) in enumerate(rstate["groups"])
            if ctype == "subtitle"
        }
        if sub_idxs and sub_idxs.issubset(rstate["selected"]):
            rstate["selected"] -= sub_idxs
        else:
            rstate["selected"] |= sub_idxs
        await query.answer()
    elif action == "rev":
        rstate["selected"] = set(range(len(rstate["groups"]))) - rstate["selected"]
        await query.answer()
    elif action == "done":
        await query.answer()
        rstate["done"] = True
        return
    elif action == "close":
        await query.answer()
        rstate["selected"] = set()
        rstate["closed"] = True
        rstate["done"] = True
        return

    await edit_message(message, rstate["text_func"](), _rs_menu(rstate))


async def get_remove_stream_selection(listener, probe_file):
    streams = await get_streams(probe_file)
    if not streams:
        return None

    groups = []
    for s in streams:
        ctype = s.get("codec_type", "").lower()
        if ctype not in ("video", "audio", "subtitle"):
            continue
        lang = None if ctype == "video" else s.get("tags", {}).get("language", "und")
        for g in groups:
            if g[0] == ctype and g[1] == lang:
                g[2].append(s.get("index"))
                break
        else:
            groups.append([ctype, lang, [s.get("index")]])
    if not groups:
        return None

    tag = listener.message.from_user.mention
    start_time = time()
    rstate = {
        "groups": groups,
        "selected": set(),
        "user_id": listener.user_id,
        "done": False,
        "closed": False,
    }
    rstate["text_func"] = lambda: _rs_text(
        tag, rstate, max(0, RS_TIMEOUT - (time() - start_time))
    )
    msg = await send_message(listener.message, rstate["text_func"](), _rs_menu(rstate))
    mid = msg.id
    rs_dict[mid] = rstate
    update_time = start_time

    while not rstate["done"]:
        await sleep(0.5)
        elapsed = time() - start_time
        if elapsed > RS_TIMEOUT:
            rstate["closed"] = True
            break
        if time() - update_time > 10:
            update_time = time()
            with suppress(Exception):
                await edit_message(msg, rstate["text_func"](), _rs_menu(rstate))

    with suppress(Exception):
        await delete_message(msg)
    rs_dict.pop(mid, None)

    if rstate["closed"] or not rstate["selected"]:
        return None
    return [groups[i] for i in rstate["selected"]]
