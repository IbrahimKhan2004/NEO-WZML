# This file is a part of NEO-WZML (github.com/irisXDR/NEO-WZML)

from asyncio import sleep
from contextlib import suppress
from time import time

from bot.helper.ext_utils.bot_utils import new_task
from bot.helper.ext_utils.media_utils import get_streams
from bot.helper.ext_utils.metadata_utils import MetadataProcessor
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.telegram_helper.message_utils import delete_message, edit_message, send_message

SSO_TIMEOUT = 15 * 60
sso_dict = {}


def get_final_subtitle_stream_order(sstate):
    selected = sstate["ordered_selection"]
    unselected = [i for i in range(len(sstate["subtitle_streams"])) if i not in selected]
    return selected + unselected


def _sso_text(tag, sstate, time_left):
    full_order = get_final_subtitle_stream_order(sstate)
    order_lines = []
    for rank, idx in enumerate(full_order, start=1):
        stream = sstate["subtitle_streams"][idx]
        order_lines.append(f"{rank}. {stream['label']}")

    status_line = "\n".join(order_lines)

    return (
        f"{tag},\n\n"
        "<b>Select Subtitle streams in order!</b>\n"
        f"<b>Timeout:</b> {round(time_left // 60)} Min\n\n"
        f"{status_line}"
    )


def _sso_menu(sstate):
    buttons = ButtonMaker()
    for idx, stream in enumerate(sstate["subtitle_streams"]):
        if idx in sstate["ordered_selection"]:
            rank = sstate["ordered_selection"].index(idx) + 1
            btn_label = f"✅ {rank}. {stream['label']}"
        else:
            btn_label = stream["label"]
        buttons.data_button(btn_label, f"sso tgl {idx}")
    buttons.data_button("🔄 Reset Order", "sso reset", "l_body")
    buttons.data_button("Done", "sso done", "footer")
    buttons.data_button("❌ Close", "sso close", "footer")
    return buttons.build_menu(2, lb_cols=1, f_cols=2)


@new_task
async def edit_subtitle_swap_selection(client, query):
    message = query.message
    mid = message.id
    sstate = sso_dict.get(mid)
    if not sstate:
        return await query.answer()
    if query.from_user.id != sstate["user_id"]:
        return await query.answer("Not Yours!", show_alert=True)

    parts = query.data.split()
    action = parts[1]

    if action == "tgl":
        idx = int(parts[2])
        if idx in sstate["ordered_selection"]:
            sstate["ordered_selection"].remove(idx)
        else:
            sstate["ordered_selection"].append(idx)
        await query.answer()
    elif action == "reset":
        sstate["ordered_selection"].clear()
        await query.answer("Subtitle stream selection reset!")
    elif action == "done":
        await query.answer()
        sstate["done"] = True
        return
    elif action == "close":
        await query.answer()
        sstate["ordered_selection"].clear()
        sstate["closed"] = True
        sstate["done"] = True
        return

    await edit_message(message, sstate["text_func"](), _sso_menu(sstate))


async def get_subtitle_swap_selection(listener, probe_file):
    streams = await get_streams(probe_file)
    if not streams:
        return None

    subtitle_streams = []
    for s in streams:
        if s.get("codec_type", "").lower() == "subtitle":
            lang = (s.get("tags") or {}).get("language", "und")
            if lang in (None, "und", "unknown", "none", ""):
                lang_name = "unknown"
            else:
                lang_name = MetadataProcessor.convert_lang_code(lang)
            subtitle_streams.append({
                "index": s.get("index"),
                "lang": lang_name,
                "codec": s.get("codec_name", ""),
                "label": lang_name,
            })

    if len(subtitle_streams) < 2:
        return None

    label_counts = {}
    for sub in subtitle_streams:
        label_counts[sub["label"]] = label_counts.get(sub["label"], 0) + 1

    if any(count > 1 for count in label_counts.values()):
        lang_indices = {}
        for sub in subtitle_streams:
            lbl = sub["label"]
            if label_counts[lbl] > 1:
                lang_indices[lbl] = lang_indices.get(lbl, 0) + 1
                sub["label"] = f"{lbl} ({lang_indices[lbl]})"

    tag = (
        listener.message.from_user.mention
        if getattr(listener.message, "from_user", None)
        else getattr(listener, "tag", "User")
    )
    start_time = time()
    sstate = {
        "subtitle_streams": subtitle_streams,
        "ordered_selection": [],
        "user_id": listener.user_id,
        "done": False,
        "closed": False,
    }
    sstate["text_func"] = lambda: _sso_text(
        tag, sstate, max(0, SSO_TIMEOUT - (time() - start_time))
    )
    msg = await send_message(listener.message, sstate["text_func"](), _sso_menu(sstate))
    mid = msg.id
    sso_dict[mid] = sstate
    update_time = start_time

    while not sstate["done"]:
        await sleep(0.5)
        if getattr(listener, "is_cancelled", False):
            sstate["closed"] = True
            break
        elapsed = time() - start_time
        if elapsed > SSO_TIMEOUT:
            sstate["closed"] = True
            break
        if time() - update_time > 10:
            update_time = time()
            with suppress(Exception):
                await edit_message(msg, sstate["text_func"](), _sso_menu(sstate))

    with suppress(Exception):
        await delete_message(msg)
    sso_dict.pop(mid, None)

    if sstate["closed"]:
        return None

    final_order = get_final_subtitle_stream_order(sstate)
    if final_order == list(range(len(subtitle_streams))):
        return None

    return [subtitle_streams[i]["index"] for i in final_order]
