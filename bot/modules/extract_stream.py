# This file is a part of NEO-WZML (github.com/irisXDR/NEO-WZML)

from asyncio import sleep
from contextlib import suppress
from time import time

from bot.helper.ext_utils.bot_utils import new_task
from bot.helper.ext_utils.media_utils import get_streams
from bot.helper.ext_utils.metadata_utils import MetadataProcessor
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.telegram_helper.message_utils import delete_message, edit_message, send_message

ES_TIMEOUT = 15 * 60
es_dict = {}


def _group_label(ctype, lang):
    if ctype == "video":
        return "Video"
    if lang in (None, "und", "unknown", "none", ""):
        lang_name = "unknown"
    else:
        lang_name = MetadataProcessor.convert_lang_code(lang)
    return f"{ctype.capitalize()} - {lang_name}"


def _es_text(tag, estate, time_left):
    count = len(estate["selected"])
    status_line = (
        "No streams selected yet."
        if count == 0
        else f"{count} stream(s) selected for extraction."
    )
    return (
        f"{tag},\n\n"
        "<b>Select the stream(s) you want to extract!</b>\n"
        f"<b>Timeout:</b> {round(time_left // 60)} Min\n\n"
        f"{status_line}"
    )


def _es_menu(estate):
    buttons = ButtonMaker()
    for idx, (ctype, lang, _) in enumerate(estate["groups"]):
        tick = "✅ " if idx in estate["selected"] else ""
        buttons.data_button(f"{tick}{_group_label(ctype, lang)}", f"ess tgl {idx}")
    buttons.data_button("🎵 All Audio", "ess allaudio", "f_body")
    buttons.data_button("📜 All Subtitles", "ess allsub", "f_body")
    del_tick = "✅ " if estate["delete_video"] else ""
    buttons.data_button(f"{del_tick}🗑️ Delete Main Video", "ess delvid", "f_body")
    buttons.data_button("🔄 Reverse Selection", "ess rev", "l_body")
    buttons.data_button("Done", "ess done", "footer")
    buttons.data_button("❌ Close", "ess close", "footer")
    return buttons.build_menu(2, fb_cols=2, lb_cols=1, f_cols=2)


@new_task
async def edit_extract_stream_selection(client, query):
    message = query.message
    mid = message.id
    estate = es_dict.get(mid)
    if not estate:
        return await query.answer()
    if query.from_user.id != estate["user_id"]:
        return await query.answer("Not Yours!", show_alert=True)

    parts = query.data.split()
    action = parts[1]

    if action == "tgl":
        idx = int(parts[2])
        estate["selected"].symmetric_difference_update({idx})
        await query.answer()
    elif action == "allaudio":
        audio_idxs = {
            i for i, (ctype, _, _) in enumerate(estate["groups"]) if ctype == "audio"
        }
        if audio_idxs and audio_idxs.issubset(estate["selected"]):
            estate["selected"] -= audio_idxs
        else:
            estate["selected"] |= audio_idxs
        await query.answer()
    elif action == "allsub":
        sub_idxs = {
            i
            for i, (ctype, _, _) in enumerate(estate["groups"])
            if ctype == "subtitle"
        }
        if sub_idxs and sub_idxs.issubset(estate["selected"]):
            estate["selected"] -= sub_idxs
        else:
            estate["selected"] |= sub_idxs
        await query.answer()
    elif action == "delvid":
        estate["delete_video"] = not estate["delete_video"]
        await query.answer()
    elif action == "rev":
        estate["selected"] = set(range(len(estate["groups"]))) - estate["selected"]
        await query.answer()
    elif action == "done":
        await query.answer()
        estate["done"] = True
        return
    elif action == "close":
        await query.answer()
        estate["selected"] = set()
        estate["closed"] = True
        estate["done"] = True
        return

    await edit_message(message, estate["text_func"](), _es_menu(estate))


async def get_extract_stream_selection(listener, probe_file):
    streams = await get_streams(probe_file)
    if not streams:
        return None, False

    groups = []
    for s in streams:
        ctype = s.get("codec_type", "").lower()
        if ctype not in ("video", "audio", "subtitle"):
            continue
        lang = None if ctype == "video" else (s.get("tags") or {}).get("language", "und")
        for g in groups:
            if g[0] == ctype and g[1] == lang:
                g[2].append(s.get("index"))
                break
        else:
            groups.append([ctype, lang, [s.get("index")]])
    if not groups:
        return None, False

    tag = (
        listener.message.from_user.mention
        if getattr(listener.message, "from_user", None)
        else getattr(listener, "tag", "User")
    )
    start_time = time()
    estate = {
        "groups": groups,
        "selected": set(),
        "delete_video": False,
        "user_id": listener.user_id,
        "done": False,
        "closed": False,
    }
    estate["text_func"] = lambda: _es_text(
        tag, estate, max(0, ES_TIMEOUT - (time() - start_time))
    )
    msg = await send_message(listener.message, estate["text_func"](), _es_menu(estate))
    mid = msg.id
    es_dict[mid] = estate
    update_time = start_time

    while not estate["done"]:
        await sleep(0.5)
        elapsed = time() - start_time
        if elapsed > ES_TIMEOUT:
            estate["closed"] = True
            break
        if time() - update_time > 10:
            update_time = time()
            with suppress(Exception):
                await edit_message(msg, estate["text_func"](), _es_menu(estate))

    with suppress(Exception):
        await delete_message(msg)
    es_dict.pop(mid, None)

    if estate["closed"] or not estate["selected"]:
        return None, False
    return [groups[i] for i in estate["selected"]], estate["delete_video"]
