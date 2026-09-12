#!/usr/bin/env python3
# This file is a part of NEO-WZML
# Custom Theme: Carsota
# Hinglish • Clean • Less Emoji

class NeoStyle:

    ST_BN1_NAME = "Car"
    ST_BN1_URL = "https://t.me/telegram"
    ST_BN2_NAME = "sota"
    ST_BN2_URL = "https://t.me/telegram"

    ST_MSG = """<i>Ye bot aapke links, files aur torrents ko Google Drive, rclone cloud, Telegram ya DDL servers par mirror kar sakta hai.</i>
<b>Available commands dekhne ke liye {help_command} type karein.</b>"""

    ST_BOTPM = """<i>Ab bot aapki files aur links yahin send karega. Start using the bot...</i>"""

    ST_UNAUTH = """<i>Ab bot aapki files aur links yahin send karega. Start using the bot...</i>"""

    OWN_TOKEN_GENERATE = """<b>Ye Temporary Token aapka nahi hai!</b>

<i>Please apna token generate karein.</i>"""

    USED_TOKEN = """<b>Ye Temporary Token already use ho chuka hai!</b>

<i>Please ek naya token generate karein.</i>"""

    LOGGED_PASSWORD = """<b>Bot Password se already logged in hai.</b>

<i>Temporary Token accept karne ki zarurat nahi hai.</i>"""

    ACTIVATE_BUTTON = "Activate Temporary Token"

    TOKEN_MSG = """<b><u>Temporary Login Token Generated!</u></b>
<b>Token:</b> <code>{token}</code>
<b>Validity:</b> {validity}"""

    ACTIVATED = "Activated"
    LOGGED_IN = "<b>Bot already logged in hai!</b>"
    INVALID_PASS = "<b>Password incorrect hai!</b>\n\n<i>Please correct password enter karein.</i>"
    PASS_LOGGED = "<b>Bot Permanent Login Successfully!</b>"
    LOGIN_USED = "<b>Bot Login:</b>\n\n<code>/cmd [password]</code>"

    LOG_DISPLAY_BT = "Log Display"
    WEB_PASTE_BT = "Web Paste (SB)"

    BASIC_BT = "Basic"
    USER_BT = "Users"
    MICS_BT = "Misc"
    O_S_BT = "Owner & Sudos"
    CLOSE_BT = "Close"

    HELP_HEADER = """<b><i>Help Guide</i></b>

<b>Note:</b> Kisi bhi command par click karke uski details dekhein."""

    BOT_STATS = """<blockquote><b><i>BOT STATISTICS</i></b></blockquote>
 • <b>Bot Uptime:</b> {bot_uptime}

 • <b>RAM:</b>
 • {ram_bar} {ram}%
 • <b>Used:</b> {ram_u} | <b>Free:</b> {ram_f} | <b>Total:</b> {ram_t}

 • <b>SWAP:</b>
 • {swap_bar} {swap}%
 • <b>Used:</b> {swap_u} | <b>Free:</b> {swap_f} | <b>Total:</b> {swap_t}

 • <b>DISK:</b>
 • {disk_bar} {disk}%
 • <b>Total Read:</b> {disk_read}
 • <b>Total Write:</b> {disk_write}
 • <b>Used:</b> {disk_u} | <b>Free:</b> {disk_f} | <b>Total:</b> {disk_t}
"""

    SYS_STATS = """<blockquote><b><i>SYSTEM INFO</i></b></blockquote>
 • <b>OS Uptime:</b> {os_uptime}
 • <b>OS Version:</b> {os_version}
 • <b>OS Arch:</b> {os_arch}

<blockquote><b><i>NETWORK STATS</i></b></blockquote>
 • <b>Upload:</b> {up_data}
 • <b>Download:</b> {dl_data}
 • <b>Packets Sent:</b> {pkt_sent}k
 • <b>Packets Received:</b> {pkt_recv}k
 • <b>Total I/O:</b> {tl_data}

 • <b>CPU:</b>
 • {cpu_bar} {cpu}%
 • <b>CPU Frequency:</b> {cpu_freq}
 • <b>System Load:</b> {sys_load}
 • <b>P-Core(s):</b> {p_core} | <b>V-Core(s):</b> {v_core}
 • <b>Total Core(s):</b> {total_core}
 • <b>Usable CPU(s):</b> {cpu_use}
"""

    REPO_STATS = """<blockquote><b><i>REPOSITORY INFO</i></b></blockquote>
 • <b>Last Updated:</b> {last_commit}
 • <b>Current Version:</b> {bot_version}
 • <b>Latest Version:</b> {lat_version}
 • <b>Last ChangeLog:</b> {commit_details}

<b>Remarks:</b> <code>{remarks}</code>
"""

    BOT_LIMITS = """<blockquote><b><i>BOT LIMITS</i></b></blockquote>
 • <b>Direct:</b> {DL} GB
 • <b>Torrent:</b> {TL} GB
 • <b>GDrive:</b> {GL} GB
 • <b>YT-DLP:</b> {YL} GB
 • <b>Playlist:</b> {PL}
 • <b>Mega:</b> {ML} GB
 • <b>Clone:</b> {CL} GB
 • <b>Leech:</b> {LL} GB
 • <b>RClone:</b> {RL} GB
 • <b>JDownloader:</b> {JL} GB
 • <b>Archive:</b> {AL} GB
 • <b>Extract:</b> {EL} GB
 • <b>Storage Threshold:</b> {TS} GB
"""

    RESTARTING = "<i>Bot restart ho raha hai...</i>"

    RESTART_SUCCESS = """<blockquote><b><i>Bot Restarted Successfully!</i></b></blockquote>
 • <b>Date:</b> {date}
 • <b>Time:</b> {time}
 • <b>TimeZone:</b> {timz}
 • <b>Version:</b> {version}"""

    RESTARTED = """<blockquote><b><i>Bot Restarted</i></b></blockquote>
 • <b>Date:</b> {date}
 • <b>Time:</b> {time}
 • <b>TimeZone:</b> {timz}
 • <b>Version:</b> {version}"""

    PING = "<i>Ping check start ho raha hai...</i>"
    PING_VALUE = "<b>Pong</b>\n<code>{value} ms</code>"

    PM_START = "✦ <b><u>Task Started</u></b>\n\n • <b>Link:</b> <a href='{msg_link}'>Open</a>"

    L_LOG_START = """✦ <b><u>Leech Started</u></b>

 • <b>User:</b> {mention} ( #ID{uid} )
 • <b>Source:</b> <a href='{msg_link}'>Open</a>"""

    LINKS_START = """<b><i>Task Started</i></b>
 • <b>Mode:</b> {Mode}
 • <b>By:</b> {Tag}

"""

    LINKS_SOURCE = """✦ <b>Source</b>
 • <b>Added On:</b> {On}
------------------------------------------
{Source}
------------------------------------------

"""

    NAME = "<blockquote><b><i>{Name}</i></b></blockquote>\n\n"
    SIZE = " • <b>Size:</b> {Size}\n"
    ELAPSE = " • <b>Elapsed:</b> {Time}\n"
    MODE = " • <b>Mode:</b> {Mode}\n"

    L_TOTAL_FILES = " • <b>Total Files:</b> {Files}\n"
    L_CORRUPTED_FILES = " • <b>Corrupted Files:</b> {Corrupt}\n"
    L_CC = " • <b>By:</b> {Tag}\n\n"

    PM_BOT_MSG = "✦ <b><i>Files upar send kar di gayi hain.</i></b>"
    L_BOT_MSG = "✦ <b><i>Files Bot PM mein send kar di gayi hain.</i></b>"
    L_LL_MSG = "✦ <b><i>Files send ho gayi hain. Links se access karein.</i></b>\n"

    M_TYPE = " • <b>Type:</b> {Mimetype}\n"
    M_SUBFOLD = " • <b>SubFolders:</b> {Folder}\n"
    TOTAL_FILES = " • <b>Files:</b> {Files}\n"
    RCPATH = " • <b>Path:</b> <code>{RCpath}</code>\n"
    M_CC = " • <b>By:</b> {Tag}\n\n"

    M_BOT_MSG = "✦ <b><i>Links Bot PM mein send kar diye gaye hain.</i></b>"

    CLOUD_LINK = "Cloud Link"
    SAVE_MSG = "Save Message"
    RCLONE_LINK = "RClone Link"
    DDL_LINK = "{Serv} Link"
    SOURCE_URL = "Source Link"
    INDEX_LINK_F = "Index Link"
    INDEX_LINK_D = "Index Link"
    VIEW_LINK = "View Link"
    CHECK_PM = "View in Bot PM"
    CHECK_LL = "View in Links Log"
    MEDIAINFO_LINK = "MediaInfo"
    SCREENSHOTS = "Screenshots"

    STATUS_NAME = "<b>{TaskNum}. <i>{Name}</i></b>"

    BAR = "\n • {Bar}"
    PROCESSED = "\n • <b>Done:</b> {Processed}"
    STATUS = '\n • <b>Status:</b> <a href="{Url}">{Status}</a>'
    ETA = "\n • <b>ETA:</b> {Eta}"
    SPEED = "\n • <b>Speed:</b> {Speed}"
    ELAPSED = "\n • <b>Elapsed:</b> {Elapsed}"
    ENGINE = "\n • <b>Engine:</b> {Engine}"
    STA_MODE = "\n • <b>Mode:</b> {Mode}"
    SEEDERS = "\n • <b>Seeders:</b> {Seeders} | "
    LEECHERS = "<b>Leechers:</b> {Leechers}"

    SEED_SIZE = "\n • <b>Size:</b> {Size}"
    SEED_SPEED = "\n • <b>Speed:</b> {Speed} | "
    UPLOADED = "<b>Uploaded:</b> {Upload}"
    RATIO = "\n • <b>Ratio:</b> {Ratio} | "
    TIME = "<b>Time:</b> {Time}"
    SEED_ENGINE = "\n • <b>Engine:</b> {Engine}"

    STATUS_SIZE = "\n • <b>Size:</b> {Size}"
    NON_ENGINE = "\n • <b>Engine:</b> {Engine}"

    USER = "\n • <b>User:</b> <code>{User}</code>"
    ID = "\n • <b>User ID:</b> <code>{Id}</code>"
    BTSEL = "\n • <b>Select:</b> {Btsel}"
    CANCEL = "\n • {Cancel}\n\n"

    FOOTER = "<blockquote><b><i>Bot Stats</i></b></blockquote>\n"
    TASKS = " • <b>Tasks:</b> {Tasks}\n"
    BOT_TASKS = " • <b>Tasks:</b> {Tasks}/{Ttask} | <b>Available:</b> {Free}\n"

    Cpu = " • <b>CPU:</b> {cpu}% | "
    FREE = "<b>Free:</b> {free} [{free_p}%]"
    Ram = "\n • <b>RAM:</b> {ram}% | "
    uptime = "<b>UPTIME:</b> {uptime}"
    DL = "\n • <b>DL:</b> {DL}/s | "
    UL = "<b>UL:</b> {UL}/s"

    PREVIOUS = "❮❮"
    REFRESH = "Page {Page}"
    NEXT = "❯❯"

    STOP_DUPLICATE = """<b>File/Folder already Drive mein available hai.</b>

{content} results mile hain:"""

    COUNT_MSG = "<b>Counting:</b> <code>{LINK}</code>"
    COUNT_NAME = "<b><i>{COUNT_NAME}</i></b>\n\n"
    COUNT_SIZE = " • <b>Size:</b> {COUNT_SIZE}\n"
    COUNT_TYPE = " • <b>Type:</b> {COUNT_TYPE}\n"
    COUNT_SUB = " • <b>SubFolders:</b> {COUNT_SUB}\n"
    COUNT_FILE = " • <b>Files:</b> {COUNT_FILE}\n"
    COUNT_CC = " • <b>By:</b> {COUNT_CC}\n"

    LIST_SEARCHING = "<b><i>{NAME}</i> search ho raha hai...</b>"
    LIST_FOUND = "<b><i>{NAME}</i> ke {NO} results mile.</b>"
    LIST_NOT_FOUND = "<b><i>{NAME}</i> ka koi result nahi mila.</b>"

    NO_ACTIVE_DL = """<i>Abhi koi active download nahi hai.</i>

<blockquote><b><i>Bot Stats</i></b></blockquote>
 • <b>CPU:</b> {cpu}% | <b>Free:</b> {free} [{free_p}%]
 • <b>RAM:</b> {ram} | <b>UPTIME:</b> {uptime}
"""

    USER_SETTING = """✦ <b><u>User Settings</u></b>

 • <b>Name:</b> {NAME} ( <code>{ID}</code> )
 • <b>Username:</b> {USERNAME}
 • <b>Telegram DC:</b> {DC}"""

    UNIVERSAL = """✦ <b><u>Universal Settings: {NAME}</u></b>

 • <b>YT-DLP Options:</b> <b><code>{YT}</code></b>
 • <b>Daily Tasks:</b> <code>{DT}</code> per day
 • <b>Last Bot Used:</b> <code>{LAST_USED}</code>
 • <b>User Session:</b> <code>{USESS}</code>
 • <b>MediaInfo Mode:</b> <code>{MEDIAINFO}</code>
 • <b>Save Mode:</b> <code>{SAVE_MODE}</code>
 • <b>User Bot PM:</b> <code>{BOT_PM}</code>"""

    MIRROR = """✦ <b><u>Mirror/Clone Settings: {NAME}</u></b>

 • <b>RClone Config:</b> <i>{RCLONE}</i>
 • <b>Mirror Prefix:</b> <code>{MPREFIX}</code>
 • <b>Mirror Suffix:</b> <code>{MSUFFIX}</code>
 • <b>Mirror Name Swap:</b> <code>{MREMNAME}</code>
 • <b>DDL Server(s):</b> <i>{DDL_SERVER}</i>
 • <b>User TD Mode:</b> <i>{TMODE}</i>
 • <b>Total User TD(s):</b> <i>{USERTD}</i>
 • <b>Daily Mirror:</b> <code>{DM}</code> per day"""

    LEECH = """✦ <b><u>Leech Settings: {NAME}</u></b>

 • <b>Daily Leech:</b> <code>{DL}</code> per day
 • <b>Leech Type:</b> <i>{LTYPE}</i>
 • <b>Custom Thumbnail:</b> <i>{THUMB}</i>
 • <b>Equal Splits:</b> <i>{EQUAL_SPLIT}</i>
 • <b>Leech Caption:</b> <code>{LCAPTION}</code>
 • <b>Leech Prefix:</b> <code>{LPREFIX}</code>
 • <b>Leech Suffix:</b> <code>{LSUFFIX}</code>
 • <b>Caption Style:</b> <i>{LCAPTIONSTYLE}</i>
 • <b>Leech Dumps:</b> <code>{LDUMP}</code>
 • <b>Leech Name Swap:</b> <code>{LREMNAME}</code>
 • <b>Leech Metadata:</b> <code>{LMETA}</code>"""