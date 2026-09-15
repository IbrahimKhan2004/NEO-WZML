# This file is a part of NEO-WZML (github.com/irisXDR/NEO-WZML)

from asyncio import sleep
from contextlib import suppress
from functools import partial
from time import time

from pyrogram.filters import create
from pyrogram.handlers import MessageHandler

from bot.core.tg_client import TgClient
from bot.helper.ext_utils.bot_utils import new_task
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.telegram_helper.message_utils import (
    delete_message,
    edit_message,
    send_message,
)

VT_TIMEOUT = 150
vt_dict = {}
handler_dict = {}


def _vt_menu(vstate):
    buttons = ButtonMaker()
    tick = "✅ " if vstate["merge_video"] else ""
    buttons.data_button(f"{tick}Video Merge", "vt mv")
    es_tick = "✅ " if vstate["extract_stream"] else ""
    buttons.data_button(f"{es_tick}Extract Streams", "vt es")
    rs_tick = "✅ " if vstate["remove_stream"] else ""
    buttons.data_button(f"{rs_tick}Remove Stream", "vt rs")
    ca_tick = "✅ " if vstate["convert_audio"] else ""
    buttons.data_button(f"{ca_tick}Convert Audio", "vt ca")
    buttons.data_button("Done", "vt done")
    buttons.data_button("Close", "vt close")
    return buttons.build_menu(1)


def _vt_text(tag, time_left):
    return (
        f"<b>Video Tools Settings for</b> {tag}\n\n"
        f"<b>Timeout:</b> {round(time_left)} Seconds"
    )


AUDIO_FORMATS = ["AAC", "MP3", "FLAC", "OPUS", "AC3", "WAV"]
AUDIO_BITRATES = ["40k", "64k", "96k", "128k", "192k", "256k", "320k"]


def _ca_menu_text(vstate):
    fmt = vstate["audio_format"] or "None"
    bitrate = vstate["audio_bitrate"] or "Original"
    return (
        "<b>Configure Audio Conversion!</b>\n\n"
        f"Format: {fmt}\n"
        f"Bitrate: {bitrate}"
    )


def _ca_menu_buttons():
    buttons = ButtonMaker()
    buttons.data_button("Format", "vt cafmt")
    buttons.data_button("Bitrate", "vt cabr")
    buttons.data_button("Back", "vt caback")
    buttons.data_button("Done", "vt cadone")
    buttons.data_button("Close", "vt close", "footer")
    return buttons.build_menu(2, f_cols=1)


def _ca_format_text(vstate):
    return (
        "<b>Select the desired audio format!</b>\n"
        f"Current Selection: {vstate['audio_format'] or 'None'}"
    )


def _ca_format_buttons(vstate):
    buttons = ButtonMaker()
    for fmt in AUDIO_FORMATS:
        tick = "✅ " if vstate["audio_format"] == fmt else ""
        buttons.data_button(f"{tick}{fmt}", f"vt fmt_{fmt}")
    buttons.data_button("Back", "vt fmtback")
    buttons.data_button("Done", "vt fmtdone")
    return buttons.build_menu(2)


def _ca_bitrate_text(vstate):
    return (
        "<b>Select the desired audio bitrate!</b>\n"
        f"Current Selection: {vstate['audio_bitrate'] or 'Original'}"
    )


def _ca_bitrate_buttons(vstate):
    buttons = ButtonMaker()
    for br in AUDIO_BITRATES:
        tick = "✅ " if vstate["audio_bitrate"] == br else ""
        buttons.data_button(f"{tick}{br}", f"vt br_{br}")
    buttons.data_button("Back", "vt brback")
    buttons.data_button("Done", "vt brdone")
    return buttons.build_menu(2)


def _filename_prompt_menu():
    buttons = ButtonMaker()
    buttons.data_button("Back", "vt back")
    buttons.data_button("Close", "vt close")
    return buttons.build_menu(1)


async def _filename_listener(client, message, mid):
    vstate = vt_dict.get(mid)
    handler_dict[mid] = False
    name = message.text.strip()
    await delete_message(message)
    if not vstate:
        return
    if vstate.get("handler"):
        client.remove_handler(*vstate["handler"])
        vstate["handler"] = None
    if "." not in name:
        await send_message(
            message, "Filename must include an extension! Send it again."
        )
        handler_dict[mid] = True
        pfunc = partial(_filename_listener, mid=mid)
        vstate["handler"] = client.add_handler(
            MessageHandler(pfunc, filters=create(_filter(vstate, message.chat.id))),
            group=-1,
        )
        return
    vstate["merge_name"] = name
    vstate["merge_video"] = True
    vstate["stage"] = "menu"
    settings_msg = await client.get_messages(message.chat.id, mid)
    await edit_message(settings_msg, vstate["text_func"](), _vt_menu(vstate))


def _filter(vstate, chat_id):
    async def event_filter(_, __, event):
        user = event.from_user or event.sender_chat
        return bool(
            user
            and user.id == vstate["user_id"]
            and event.chat.id == chat_id
            and event.text
        )

    return event_filter


@new_task
async def edit_video_tool(client, query):
    message = query.message
    mid = message.id
    vstate = vt_dict.get(mid)
    if not vstate:
        return await query.answer()
    if query.from_user.id != vstate["user_id"]:
        return await query.answer("Not Yours!", show_alert=True)

    action = query.data.split()[1]

    if action == "mv" and not vstate["merge_video"]:
        await query.answer()
        vstate["stage"] = "filename"
        await edit_message(
            message,
            "Please send a name for the merged video file. Make sure to include "
            "the extension.\n<b>Example:</b> <code>MyMergedVideo.mp4</code>\n\n"
            "<b>Note:</b> Files are naturally sorted (e.g. 1.mp4, 2.mp4... 10.mp4) "
            "before merging.",
            _filename_prompt_menu(),
        )
        handler_dict[mid] = True
        pfunc = partial(_filename_listener, mid=mid)
        vstate["handler"] = client.add_handler(
            MessageHandler(pfunc, filters=create(_filter(vstate, message.chat.id))),
            group=-1,
        )
    elif action == "mv" and vstate["merge_video"]:
        vstate["merge_video"] = False
        vstate["merge_name"] = ""
        await query.answer("Video Merge disabled!")
        await edit_message(message, vstate["text_func"](), _vt_menu(vstate))
    elif action == "es" and not vstate["extract_stream"]:
        vstate["extract_stream"] = True
        await query.answer(
            "⏳ You will be able to select streams after the download is complete",
            show_alert=True,
        )
        await edit_message(message, vstate["text_func"](), _vt_menu(vstate))
    elif action == "es" and vstate["extract_stream"]:
        vstate["extract_stream"] = False
        await query.answer("Extract Streams disabled!")
        await edit_message(message, vstate["text_func"](), _vt_menu(vstate))
    elif action == "rs" and not vstate["remove_stream"]:
        vstate["remove_stream"] = True
        await query.answer(
            "⏳ You will be able to select streams after the download is complete",
            show_alert=True,
        )
        await edit_message(message, vstate["text_func"](), _vt_menu(vstate))
    elif action == "rs" and vstate["remove_stream"]:
        vstate["remove_stream"] = False
        await query.answer("Remove Stream disabled!")
        await edit_message(message, vstate["text_func"](), _vt_menu(vstate))
    elif action == "ca":
        await query.answer()
        vstate["stage"] = "ca_menu"
        await edit_message(message, _ca_menu_text(vstate), _ca_menu_buttons())
    elif action == "cafmt":
        await query.answer()
        vstate["stage"] = "ca_format"
        await edit_message(message, _ca_format_text(vstate), _ca_format_buttons(vstate))
    elif action == "cabr":
        if vstate["audio_format"] == "FLAC":
            return await query.answer(
                "Bitrate is not applicable for lossless FLAC!", show_alert=True
            )
        await query.answer()
        vstate["stage"] = "ca_bitrate"
        await edit_message(message, _ca_bitrate_text(vstate), _ca_bitrate_buttons(vstate))
    elif action == "caback":
        await query.answer()
        vstate["convert_audio"] = bool(vstate["audio_format"] or vstate["audio_bitrate"])
        vstate["stage"] = "menu"
        await edit_message(message, vstate["text_func"](), _vt_menu(vstate))
    elif action == "cadone":
        await query.answer()
        vstate["convert_audio"] = bool(vstate["audio_format"] or vstate["audio_bitrate"])
        vstate["stage"] = "menu"
        await edit_message(message, vstate["text_func"](), _vt_menu(vstate))
    elif action.startswith("fmt_"):
        fmt = action.split("_", 1)[1]
        if vstate["audio_format"] == fmt:
            vstate["audio_format"] = ""
        else:
            vstate["audio_format"] = fmt
            if fmt == "FLAC":
                vstate["audio_bitrate"] = ""
        await query.answer()
        await edit_message(message, _ca_format_text(vstate), _ca_format_buttons(vstate))
    elif action == "fmtback" or action == "fmtdone":
        await query.answer()
        vstate["stage"] = "ca_menu"
        await edit_message(message, _ca_menu_text(vstate), _ca_menu_buttons())
    elif action.startswith("br_"):
        br = action.split("_", 1)[1]
        vstate["audio_bitrate"] = "" if vstate["audio_bitrate"] == br else br
        await query.answer()
        await edit_message(message, _ca_bitrate_text(vstate), _ca_bitrate_buttons(vstate))
    elif action == "brback" or action == "brdone":
        await query.answer()
        vstate["stage"] = "ca_menu"
        await edit_message(message, _ca_menu_text(vstate), _ca_menu_buttons())
    elif action == "back":
        await query.answer()
        vstate["stage"] = "menu"
        if vstate.get("handler"):
            client.remove_handler(*vstate["handler"])
            vstate["handler"] = None
        handler_dict[mid] = False
        await edit_message(message, vstate["text_func"](), _vt_menu(vstate))
    elif action == "close":
        await query.answer()
        vstate["merge_video"] = False
        vstate["merge_name"] = ""
        vstate["extract_stream"] = False
        vstate["remove_stream"] = False
        vstate["convert_audio"] = False
        vstate["audio_format"] = ""
        vstate["audio_bitrate"] = ""
        if vstate.get("handler"):
            client.remove_handler(*vstate["handler"])
            vstate["handler"] = None
        handler_dict[mid] = False
        vstate["done"] = True
    elif action == "done":
        await query.answer()
        if vstate.get("handler"):
            client.remove_handler(*vstate["handler"])
            vstate["handler"] = None
        handler_dict[mid] = False
        vstate["done"] = True


async def get_video_tool_settings(listener):
    tag = listener.message.from_user.mention
    start_time = time()
    vstate = {
        "merge_video": False,
        "merge_name": "",
        "extract_stream": False,
        "remove_stream": False,
        "convert_audio": False,
        "audio_format": "",
        "audio_bitrate": "",
        "stage": "menu",
        "done": False,
        "user_id": listener.user_id,
        "handler": None,
    }
    vstate["text_func"] = lambda: _vt_text(
        tag, max(0, VT_TIMEOUT - (time() - start_time))
    )
    msg = await send_message(listener.message, vstate["text_func"](), _vt_menu(vstate))
    mid = msg.id
    vt_dict[mid] = vstate
    update_time = start_time

    while not vstate["done"]:
        await sleep(0.5)
        elapsed = time() - start_time
        if elapsed > VT_TIMEOUT:
            vstate["merge_video"] = False
            vstate["merge_name"] = ""
            vstate["extract_stream"] = False
            vstate["remove_stream"] = False
            vstate["convert_audio"] = False
            vstate["audio_format"] = ""
            vstate["audio_bitrate"] = ""
            if vstate.get("handler"):
                TgClient.bot.remove_handler(*vstate["handler"])
            handler_dict[mid] = False
            break
        if vstate["stage"] == "menu" and time() - update_time > 10:
            update_time = time()
            with suppress(Exception):
                await edit_message(msg, vstate["text_func"](), _vt_menu(vstate))

    with suppress(Exception):
        await delete_message(msg)
    listener.merge_video = vstate["merge_video"]
    listener.merge_name = vstate["merge_name"]
    listener.extract_stream = vstate["extract_stream"]
    listener.remove_stream = vstate["remove_stream"]
    listener.vt_convert_audio = vstate["audio_format"].lower() if vstate["convert_audio"] else ""
    listener.vt_audio_bitrate = vstate["audio_bitrate"] if vstate["convert_audio"] else ""
    vt_dict.pop(mid, None)
    handler_dict.pop(mid, None)
