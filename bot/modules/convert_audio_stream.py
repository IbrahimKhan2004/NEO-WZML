# This file is a part of NEO-WZML (github.com/IbrahimKhan2004/NEO-WZML)

from asyncio import sleep
from contextlib import suppress
from time import time

from bot.helper.ext_utils.bot_utils import new_task
from bot.helper.ext_utils.media_utils import get_streams
from bot.helper.ext_utils.metadata_utils import MetadataProcessor
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.telegram_helper.message_utils import delete_message, edit_message, send_message

CAS_TIMEOUT = 15 * 60
cas_dict = {}


def _lang_name(lang):
    if lang in (None, "und", "unknown", "none", ""):
        return "unknown"
    return MetadataProcessor.convert_lang_code(lang)


def _cas_text(tag, castate, time_left):
    if castate["selected"]:
        status_line = "\n".join(
            f"{rank}. {_lang_name(castate['groups'][idx][0])}"
            for rank, idx in enumerate(sorted(castate["selected"]), 1)
        )
    else:
        status_line = "No streams selected yet."
    return (
        f"{tag},\n\n"
        "<b>Select Audio streams to convert!</b>\n"
        f"<b>Timeout:</b> {round(time_left // 60)} Min\n\n"
        f"{status_line}"
    )


def _cas_menu(castate):
    buttons = ButtonMaker()
    for idx, (lang, _) in enumerate(castate["groups"]):
        tick = "✅ " if idx in castate["selected"] else ""
        buttons.data_button(f"{tick}{_lang_name(lang)}", f"cas tgl {idx}")
    buttons.data_button("Done", "cas done", "footer")
    buttons.data_button("❌ Close", "cas close", "footer")
    return buttons.build_menu(2, f_cols=2)


@new_task
async def edit_convert_audio_stream_selection(client, query):
    message = query.message
    mid = message.id
    castate = cas_dict.get(mid)
    if not castate:
        return await query.answer()
    if query.from_user.id != castate["user_id"]:
        return await query.answer("Not Yours!", show_alert=True)

    parts = query.data.split()
    action = parts[1]

    if action == "tgl":
        idx = int(parts[2])
        castate["selected"].symmetric_difference_update({idx})
        await query.answer()
    elif action == "done":
        await query.answer()
        castate["done"] = True
        return
    elif action == "close":
        await query.answer()
        castate["selected"] = set()
        castate["closed"] = True
        castate["done"] = True
        return

    await edit_message(message, castate["text_func"](), _cas_menu(castate))


async def get_convert_audio_stream_selection(listener, probe_file):
    streams = await get_streams(probe_file)
    if not streams:
        return None

    audio_streams = [s for s in streams if s.get("codec_type", "").lower() == "audio"]
    if not audio_streams:
        return None

    groups = []
    for ordinal, s in enumerate(audio_streams):
        lang = (s.get("tags") or {}).get("language", "und")
        for g in groups:
            if g[0] == lang:
                g[1].append(ordinal)
                break
        else:
            groups.append([lang, [ordinal]])

    tag = (
        listener.message.from_user.mention
        if getattr(listener.message, "from_user", None)
        else getattr(listener, "tag", "User")
    )
    start_time = time()
    castate = {
        "groups": groups,
        "selected": set(),
        "user_id": listener.user_id,
        "done": False,
        "closed": False,
    }
    castate["text_func"] = lambda: _cas_text(
        tag, castate, max(0, CAS_TIMEOUT - (time() - start_time))
    )
    msg = await send_message(listener.message, castate["text_func"](), _cas_menu(castate))
    mid = msg.id
    cas_dict[mid] = castate
    update_time = start_time

    while not castate["done"]:
        await sleep(0.5)
        if getattr(listener, "is_cancelled", False):
            castate["closed"] = True
            break
        elapsed = time() - start_time
        if elapsed > CAS_TIMEOUT:
            castate["closed"] = True
            break
        if time() - update_time > 10:
            update_time = time()
            with suppress(Exception):
                await edit_message(msg, castate["text_func"](), _cas_menu(castate))

    with suppress(Exception):
        await delete_message(msg)
    cas_dict.pop(mid, None)

    if castate["closed"] or not castate["selected"]:
        return None
    return sorted({o for i in castate["selected"] for o in groups[i][1]})
