# This file is a part of NEO-WZML (github.com/irisXDR/NEO-WZML)

from asyncio import sleep
from contextlib import suppress
from time import time

from bot.helper.ext_utils.bot_utils import new_task
from bot.helper.ext_utils.media_utils import get_streams
from bot.helper.ext_utils.metadata_utils import MetadataProcessor
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.telegram_helper.message_utils import delete_message, edit_message, send_message

ASO_TIMEOUT = 15 * 60
aso_dict = {}
PAGE_SIZE = 100


def get_final_stream_order(astate):
    selected = astate["ordered_selection"]
    unselected = [i for i in range(len(astate["audio_streams"])) if i not in selected]
    return selected + unselected


def _aso_text(tag, astate, time_left):
    full_order = get_final_stream_order(astate)
    order_lines = []
    for rank, idx in enumerate(full_order, start=1):
        stream = astate["audio_streams"][idx]
        order_lines.append(f"{rank}. {stream['label']}")

    status_line = "\n".join(order_lines)

    return (
        f"{tag},\n\n"
        "<b>Select Audio streams in order!</b>\n"
        f"<b>Timeout:</b> {round(time_left // 60)} Min\n\n"
        f"{status_line}"
    )


def _aso_menu(astate):
    buttons = ButtonMaker()
    page = astate.get("page", 0)
    total_streams = len(astate["audio_streams"])
    total_pages = (total_streams + PAGE_SIZE - 1) // PAGE_SIZE

    start_idx = page * PAGE_SIZE
    end_idx = min(start_idx + PAGE_SIZE, total_streams)

    for idx in range(start_idx, end_idx):
        stream = astate["audio_streams"][idx]
        if idx in astate["ordered_selection"]:
            rank = astate["ordered_selection"].index(idx) + 1
            btn_label = f"✅ {rank}. {stream['label']}"
        else:
            btn_label = stream["label"]
        buttons.data_button(btn_label, f"aso tgl {idx}")

    if total_pages > 1:
        prev_page = (page - 1) % total_pages
        next_page = (page + 1) % total_pages
        buttons.data_button("◀️ Prev", f"aso page {prev_page}", "f_body")
        buttons.data_button(f"{page + 1}/{total_pages}", "aso page_info", "f_body")
        buttons.data_button("Next ▶️", f"aso page {next_page}", "f_body")

    buttons.data_button("🔄 Reset Order", "aso reset", "l_body")
    buttons.data_button("Done", "aso done", "footer")
    buttons.data_button("❌ Close", "aso close", "footer")

    fb_cols = 3 if total_pages > 1 else 0
    return buttons.build_menu(2, fb_cols=fb_cols, lb_cols=1, f_cols=2)


@new_task
async def edit_audio_swap_selection(client, query):
    message = query.message
    mid = message.id
    astate = aso_dict.get(mid)
    if not astate:
        return await query.answer()
    if query.from_user.id != astate["user_id"]:
        return await query.answer("Not Yours!", show_alert=True)

    parts = query.data.split()
    action = parts[1]

    if action == "tgl":
        idx = int(parts[2])
        if idx in astate["ordered_selection"]:
            astate["ordered_selection"].remove(idx)
        else:
            astate["ordered_selection"].append(idx)
        await query.answer()
    elif action == "page":
        astate["page"] = int(parts[2])
        await query.answer()
    elif action == "page_info":
        await query.answer("Use Prev/Next buttons to navigate streams", show_alert=True)
    elif action == "reset":
        astate["ordered_selection"].clear()
        await query.answer("Audio stream selection reset!")
    elif action == "done":
        await query.answer()
        astate["done"] = True
        return
    elif action == "close":
        await query.answer()
        astate["ordered_selection"].clear()
        astate["closed"] = True
        astate["done"] = True
        return

    await edit_message(message, astate["text_func"](), _aso_menu(astate))


async def get_audio_swap_selection(listener, probe_file):
    streams = await get_streams(probe_file)
    if not streams:
        return None

    audio_streams = []
    for s in streams:
        if s.get("codec_type", "").lower() == "audio":
            lang = (s.get("tags") or {}).get("language", "und")
            if lang in (None, "und", "unknown", "none", ""):
                lang_name = "unknown"
            else:
                lang_name = MetadataProcessor.convert_lang_code(lang)
            audio_streams.append({
                "index": s.get("index"),
                "lang": lang_name,
                "codec": s.get("codec_name", ""),
                "label": lang_name,
            })

    if len(audio_streams) < 2:
        tag = (
            listener.message.from_user.mention
            if getattr(listener.message, "from_user", None)
            else getattr(listener, "tag", "User")
        )
        msg_text = (
            f"{tag},\n\n"
            f"<b>Audio Swap Skipped!</b>\n"
            f"Found {len(audio_streams)} audio stream(s). Re-ordering requires at least 2 audio streams."
        )
        msg = await send_message(listener.message, msg_text)
        await sleep(4)
        with suppress(Exception):
            await delete_message(msg)
        return None

    label_counts = {}
    for a in audio_streams:
        label_counts[a["label"]] = label_counts.get(a["label"], 0) + 1

    if any(count > 1 for count in label_counts.values()):
        lang_indices = {}
        for a in audio_streams:
            lbl = a["label"]
            if label_counts[lbl] > 1:
                lang_indices[lbl] = lang_indices.get(lbl, 0) + 1
                a["label"] = f"{lbl} ({lang_indices[lbl]})"

    tag = (
        listener.message.from_user.mention
        if getattr(listener.message, "from_user", None)
        else getattr(listener, "tag", "User")
    )
    start_time = time()
    astate = {
        "audio_streams": audio_streams,
        "ordered_selection": [],
        "page": 0,
        "user_id": listener.user_id,
        "done": False,
        "closed": False,
    }
    astate["text_func"] = lambda: _aso_text(
        tag, astate, max(0, ASO_TIMEOUT - (time() - start_time))
    )
    msg = await send_message(listener.message, astate["text_func"](), _aso_menu(astate))
    mid = msg.id
    aso_dict[mid] = astate
    update_time = start_time

    while not astate["done"]:
        await sleep(0.5)
        if getattr(listener, "is_cancelled", False):
            astate["closed"] = True
            break
        elapsed = time() - start_time
        if elapsed > ASO_TIMEOUT:
            astate["closed"] = True
            break
        if time() - update_time > 10:
            update_time = time()
            with suppress(Exception):
                await edit_message(msg, astate["text_func"](), _aso_menu(astate))

    with suppress(Exception):
        await delete_message(msg)
    aso_dict.pop(mid, None)

    if astate["closed"]:
        return None

    final_order = get_final_stream_order(astate)
    if final_order == list(range(len(audio_streams))):
        return None

    return [audio_streams[i]["index"] for i in final_order]
