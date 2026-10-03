# This file is a part of NEO-WZML (github.com/IbrahimKhan2004/NEO-WZML)

from os import path as ospath
from re import I, compile as re_compile

from natsort import natsorted

from bot.helper.ext_utils.media_utils import get_streams
from bot.helper.ext_utils.metadata_utils import MetadataProcessor

EP = re_compile(r"S(\d{1,2})[ ._-]*E(\d{1,4})|\bE(?:p(?:isode)?)?[ ._-]?(\d{1,4})\b", I)
SEASON = re_compile(r"(?:season|\bS)[ ._-]?(\d{1,2})\b", I)
MULTI = re_compile(r"\b(?:multi|dual)(?:[ ._-]?audios?)?\b(?![ ._-]?subs?)", I)
SUB = re_compile(r"\b(?:[em][ ._-]?subs?|eng(?:lish)?[ ._-]?subs?|multi[ ._-]?subs?)\b", I)
RIP = re_compile(r"WEB-?DL|WEB-?Rip|Blu-?Ray|BRRip|HDRip|HDTV|DVDRip", I)


def _se(path):
    m, s = EP.search(ospath.basename(path)), SEASON.search(path)
    return (int(m[1] or (s[1] if s else 1)), int(m[2] or m[3])) if m else None


async def _name(s, cur, whole):
    (a, first), b, n = cur[0], cur[-1][0], len(cur)
    label = f"S{s} Complete" if whole and n > 1 and a == 1 and b == n else f"S{s} E{a}" + (f"-{b}" if b != a else "")
    base, st = ospath.splitext(ospath.basename(first))[0], await get_streams(first) or []
    m = EP.search(base)
    langs = lambda t: [l for l in dict.fromkeys(MetadataProcessor.convert_lang_code((x.get("tags") or {}).get("language", "und")) for x in st if x.get("codec_type") == t) if l not in ("und", "unknown", "none")]
    audio, subs = " ".join(langs("audio")), langs("subtitle")
    tag = "ESub" if "English" in subs else "MSub" if len(subs) > 1 else ""
    if m and re_compile(r"\d{3,4}p", I).search(base):  # filename already has the info: reuse it
        name = base[: m.start()] + label + (MULTI.sub(audio, base[m.end() :], 1) if audio else base[m.end() :])
        return " ".join(filter(None, [name, "" if SUB.search(name) else tag])) + ".mkv"
    v = next((x for x in st if x.get("codec_type") == "video" and not x.get("disposition", {}).get("attached_pic")), {})
    h = next((p for w, p in ((3000, 2160), (1800, 1080), (1200, 720), (800, 480)) if v.get("width", 0) >= w), v.get("height"))
    codec, rip = {"hevc": "x265 HEVC", "h264": "x264"}.get(v.get("codec_name"), v.get("codec_name", "")), RIP.search(base)
    return " ".join(filter(None, [base[: m.start()].strip(" ._-") if m else "", label, f"{h}p" if h else "", rip[0] if rip else "", codec, audio, tag])) + ".mkv"


async def plan_auto_merge(files, limit):
    files = natsorted(files)
    found = [_se(f) for f in files]
    if None in found:  # edge: no S/E info, fall back to natural order
        found = [(1, i) for i in range(1, len(files) + 1)]
    seasons = {}
    for (s, e), f in zip(found, files):
        seasons.setdefault(s, {}).setdefault(e, f)  # duplicate episode: first one wins
    plan = []
    for s, eps in sorted(seasons.items()):
        parts, cur, size = [], [], 0
        for e, f in sorted(eps.items()):
            fsize = ospath.getsize(f) * 1.01  # container overhead margin
            if cur and size + fsize > limit:
                parts, cur, size = [*parts, cur], [], 0
            cur, size = [*cur, (e, f)], size + fsize
        parts = [*parts, cur]
        if len(parts) > 1 and len(parts[-1]) * 2 < len(parts[0]):  # tiny last part: balance all parts equally
            flat, k = [x for q in parts for x in q], len(parts)
            bal = [flat[i * len(flat) // k : (i + 1) * len(flat) // k] for i in range(k)]
            parts = bal if all(sum(ospath.getsize(f) for _, f in q) * 1.01 <= limit for q in bal) else parts
        for part in parts:
            plan.append(([f for _, f in part], await _name(s, part, len(parts) == 1)))
    return plan
