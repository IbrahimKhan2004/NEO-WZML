# This file is a part of NEO-WZML (github.com/IbrahimKhan2004/NEO-WZML)

from asyncio import create_subprocess_exec
from asyncio.subprocess import DEVNULL, PIPE
from os.path import basename, splitext
from re import IGNORECASE, compile as re_compile, escape, sub
from pycountry import languages
from bot.helper.ext_utils.media_utils import get_streams
from bot.helper.ext_utils.native_lang import get_native_lang


class MetadataProcessor:
    _year_pattern = re_compile(r"(?<!\d)(?:19|20)\d{2}(?!\d)")
    _sanitize_pattern = re_compile(r'[<>:"/\\?*]')

    _sub_types = (
        "Signs & Songs", "Signs", "Songs", "Dialogue",
        "Full", "SDH", "Dubtitle", "Forced", "CC", "Commentary",
    )
    _sub_canon = {k.lower(): k for k in _sub_types}
    _sub_type_pattern = re_compile(
        rf"(?<!\w)({'|'.join(map(escape, _sub_types))})(?!\w)", IGNORECASE
    )
    _sub_bracket = re_compile(r"\[[^\[\]]+\]")

    @classmethod
    def sub_type(cls, title):
        title = title or ""
        b = [
            x
            for x in cls._sub_bracket.findall(title)
            if cls._sub_type_pattern.search(x)
        ]
        if b:
            return " ".join(b)
        found = cls._sub_type_pattern.findall(title)
        found = dict.fromkeys(cls._sub_canon[t.lower()] for t in found)
        return " ".join(f"[{k}]" for k in found)

    _fmt = {"ac3": "DD", "eac3": "DDP", "opus": "Opus", "truehd": "TrueHD"}

    @staticmethod
    def stream_bps(s):
        return s.get("bit_rate") or next(
            (v for k, v in s.get("tags", {}).items() if k[:3].upper() == "BPS"), ""
        )

    @classmethod
    async def scan_bps(cls, streams, path):
        need = {
            s["index"]: s
            for s in streams
            if s.get("codec_type") == "audio" and not cls.stream_bps(s)
        }
        if not need:
            return
        try:
            cmd = [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "a",
                "-show_entries",
                "packet=stream_index,pts_time,size",
                "-of",
                "compact=p=0",
                path,
            ]
            p = await create_subprocess_exec(*cmd, stdout=PIPE, stderr=DEVNULL)
            tot = {}
            async for line in p.stdout:
                try:
                    d = dict(x.split("=", 1) for x in line.decode().split("|"))
                    i, z = int(d["stream_index"]), int(d["size"])
                    t = float(d["pts_time"])
                except (KeyError, ValueError):
                    continue
                v = tot.setdefault(i, [0, 0, t, t])
                v[0], v[1], v[3] = v[0] + z, v[1] + 1, t
            await p.wait()
            for i, (b, n, t0, t1) in tot.items():
                if n > 1 and t1 > t0 and i in need:
                    need[i]["bit_rate"] = str(int(b * 8 * (n - 1) / (t1 - t0) / n))
        except Exception:
            pass

    @classmethod
    def audio_info(cls, s):
        c, ch = s.get("codec_name", ""), s.get("channels", 0)
        br = cls.stream_bps(s)
        return " ".join(
            filter(
                None,
                (
                    cls._fmt.get(c, c.upper()),
                    (f"{ch - 1}.1" if ch > 5 else f"{ch}.0") if ch else "",
                    f"{round(int(br) / 1000)}Kbps" if str(br).isdigit() else "",
                ),
            )
        )

    def __init__(self):
        self.vars = {}
        self.audio_streams = []
        self.subtitle_streams = []

    @staticmethod
    def convert_lang_code(lang_code):
        if not lang_code or lang_code in {"unknown", "und", "none"}:
            return lang_code
        try:
            if len(lang_code) == 2:
                lang = languages.get(alpha_2=lang_code.lower())
            elif len(lang_code) == 3:
                lang = languages.get(alpha_3=lang_code.lower())
            else:
                return lang_code
            return lang.name if lang else lang_code
        except Exception:
            return lang_code

    async def extract_file_vars(self, file_path):
        fname = basename(file_path)
        bname, ext = splitext(fname)
        self.vars = {
            "filename": fname,
            "basename": bname,
            "extension": ext.lstrip("."),
            "audiolang": "unknown",
            "audiolang_native": "unknown",
            "sublang": "none",
            "sublang_native": "none",
            "year": "",
            "vcodec": "",
            "acodec": "",
            "scodec": "",
        }
        self.audio_streams, self.subtitle_streams = [], []
        stype = ""
        try:
            streams = await get_streams(file_path) or []
            await self.scan_bps(streams, file_path)
            for s in streams:
                ctype = s.get("codec_type", "").lower()
                slang = s.get("tags", {}).get("language", "unknown")
                full_lang = self.convert_lang_code(slang)
                native_lang = get_native_lang(slang, full_lang)
                entry = {
                    "index": s.get("index", 0),
                    "language": slang,
                    "full_language": full_lang,
                    "native_language": native_lang,
                    "codec": s.get("codec_name", ""),
                    "sub_type": self.sub_type(s.get("tags", {}).get("title")),
                }
                if ctype == "audio":
                    entry["a_info"] = self.audio_info(s)
                    self.audio_streams.append(entry)
                    if self.vars["audiolang"] == "unknown" and slang != "und":
                        self.vars["audiolang"] = full_lang
                        self.vars["audiolang_native"] = native_lang
                elif ctype == "subtitle":
                    self.subtitle_streams.append(entry)
                    if self.vars["sublang"] == "none" and slang != "und":
                        self.vars["sublang"] = full_lang
                        self.vars["sublang_native"] = native_lang
                        stype = entry["sub_type"]
                elif (
                    ctype == "video"
                    and not self.vars["vcodec"]
                    and not s.get("disposition", {}).get("attached_pic")
                ):
                    self.vars["vcodec"] = s.get("codec_name", "")
        except Exception:
            pass
        m = self._year_pattern.findall(bname)
        if m:
            self.vars["year"] = m[-1]
        self.vars["title"] = sub(
            r"[._]+", " ", bname[: bname.rfind(m[-1])] if m else bname
        ).strip(" ([-")
        self.vars.update(
            a_lang=self.vars["audiolang"],
            a_lang_native=self.vars["audiolang_native"],
            s_lang=f'{self.vars["sublang"]} {stype}'.strip(),
            s_lang_native=f'{self.vars["sublang_native"]} {stype}'.strip(),
        )

    @staticmethod
    def parse_string(metadata_str):
        if not metadata_str or not isinstance(metadata_str, str):
            return {}
        parts, current, i = [], "", 0
        while i < len(metadata_str):
            if (
                metadata_str[i] == "\\"
                and i + 1 < len(metadata_str)
                and metadata_str[i + 1] == "|"
            ):
                current += "|"
                i += 2
            elif metadata_str[i] == "|":
                parts.append(current)
                current = ""
                i += 1
            else:
                current += metadata_str[i]
                i += 1
        if current:
            parts.append(current)
        return dict(p.split("=", 1) if "=" in p else (p, "") for p in parts)

    @staticmethod
    def merge_dicts(default_dict, cmd_dict):
        return {**(default_dict or {}), **(cmd_dict or {})}

    def apply_vars_to_stream(
        self,
        metadata_dict,
        stream_lang=None,
        full_lang=None,
        native_lang=None,
        stream_type="audio",
        codec="",
        sub_type="",
        a_info="",
    ):
        if not isinstance(metadata_dict, dict):
            return {}
        vars_with_stream = self.vars.copy()
        if stream_lang and stream_lang != "unknown":
            key = "audiolang" if stream_type == "audio" else "sublang"
            f_lang = full_lang or self.convert_lang_code(stream_lang)
            n_lang = native_lang or get_native_lang(stream_lang, f_lang)
            vars_with_stream[key] = f_lang
            vars_with_stream[f"{key}_native"] = n_lang
        p = "a" if stream_type == "audio" else "s"
        lang = vars_with_stream["audiolang" if p == "a" else "sublang"]
        native = vars_with_stream.get(
            f"{'audiolang' if p == 'a' else 'sublang'}_native", lang
        )
        vars_with_stream.update(
            {
                f"{p}_lang": f"{lang} {sub_type}".strip(),
                f"{p}_lang_native": f"{native} {sub_type}".strip(),
            }
        )
        if codec:
            vars_with_stream[f"{p}codec"] = codec
        vars_with_stream["a_info"] = a_info
        return {
            self.sanitize(k): (
                str(v).format(**vars_with_stream) if isinstance(v, str) else str(v)
            )
            for k, v in metadata_dict.items()
        }

    def apply_vars(self, metadata_dict):
        return self.apply_vars_to_stream(metadata_dict)

    def get_audio_metadata(self, audio_metadata_dict):
        return [
            {
                "index": s["index"],
                "metadata": self.apply_vars_to_stream(
                    audio_metadata_dict,
                    s["language"],
                    s["full_language"],
                    s.get("native_language"),
                    "audio",
                    s["codec"],
                    a_info=s["a_info"],
                ),
            }
            for s in self.audio_streams
        ]

    def get_subtitle_metadata(self, subtitle_metadata_dict):
        return [
            {
                "index": s["index"],
                "metadata": self.apply_vars_to_stream(
                    subtitle_metadata_dict,
                    s["language"],
                    s["full_language"],
                    s.get("native_language"),
                    "subtitle",
                    s["codec"],
                    s["sub_type"],
                ),
            }
            for s in self.subtitle_streams
        ]

    def sanitize(self, value):
        return self._sanitize_pattern.sub("_", str(value))[:100]

    async def process_all(
        self,
        video_metadata_dict,
        audio_metadata_dict,
        subtitle_metadata_dict,
        file_path,
    ):
        await self.extract_file_vars(file_path)
        return {
            "video": (
                self.apply_vars(video_metadata_dict) if video_metadata_dict else {}
            ),
            "audio_streams": (
                self.get_audio_metadata(audio_metadata_dict)
                if audio_metadata_dict
                else []
            ),
            "subtitle_streams": (
                self.get_subtitle_metadata(subtitle_metadata_dict)
                if subtitle_metadata_dict
                else []
            ),
            "global": {},
        }

    async def process(self, metadata_dict, file_path):
        await self.extract_file_vars(file_path)
        return self.apply_vars(metadata_dict)
