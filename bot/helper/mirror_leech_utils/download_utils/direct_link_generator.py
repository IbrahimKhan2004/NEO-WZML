# This file is a part of NEO-WZML (github.com/irisXDR/NEO-WZML)

import os as _os
from base64 import b64decode, b64encode
from cloudscraper import create_scraper
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from hashlib import sha256
from http.cookiejar import MozillaCookieJar
from json import loads
from lxml.etree import HTML
from os import path as ospath
from re import findall, fullmatch, match, search, sub
from requests import Session, post, get, RequestException
from requests.adapters import HTTPAdapter
from time import sleep, time
from urllib.parse import parse_qs, urlparse, unquote, urljoin
from urllib3.util.retry import Retry
from uuid import uuid4

from bot import LOGGER
from bot.core.config_manager import Config
from bot.helper.ext_utils.exceptions import DirectDownloadLinkException
from bot.helper.ext_utils.help_messages import PASSWORD_ERROR_MESSAGE
from bot.helper.ext_utils.links_utils import (
    is_index_link,
    is_magnet,
    is_share_link,
)
from bot.helper.ext_utils.status_utils import speed_string_to_bytes

user_agent = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"
)

# Browser-like headers for hosts that gate on them (GDFlix / HubCloud family).
HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

gofile_token_cache = None

debrid_link_supported_sites = [
    "1fichier.com",
    "anonfiles.com",
    "bayfiles.com",
    "clicknupload.link",
    "clicknupload.org",
    "clicknupload.co",
    "clicknupload.cc",
    "clicknupload.download",
    "clicknupload.club",
    "dailyuploads.net",
    "ddl.to",
    "ddownload.com",
    "ddownload.link",
    "drop.download",
    "dropbox.com",
    "dropboxusercontent.com",
    "easyupload.io",
    "emload.com",
    "file.al",
    "fileaxa.com",
    "filecat.net",
    "filedot.to",
    "filedot.xyz",
    "filextras.com",
    "filer.net",
    "filespace.com",
    "filestore.me",
    "gigapeta.com",
    "gofile.io",
    "hexupload.net",
    "hitfile.net",
    "hulkshare.com",
    "isra.cloud",
    "katfile.com",
    "kshared.com",
    "mediafire.com",
    "mega.nz",
    "mega.co.nz",
    "mexashare.com",
    "mixdrop.co",
    "mixdrop.to",
    "mixdrop.sx",
    "mixdrop.club",
    "modsbase.com",
    "nelion.me",
    "pixeldrain.com",
    "prefiles.com",
    "racaty.net",
    "rapidgator.net",
    "rapidgator.asia",
    "rg.to",
    "scribd.com",
    "send.cm",
    "sharemods.com",
    "silkfiles.com",
    "soundcloud.com",
    "streamtape.com",
    "terabox.com",
    "teraboxapp.com",
    "tezfiles.com",
    "turb.cc",
    "turb.to",
    "turbobit.net",
    "turbobit.cc",
    "turbobit.pw",
    "turbobit.online",
    "turbobit.ru",
    "turbobit.live",
    "trubobit.com",
    "turboblt.co",
    "uloz.to",
    "ulozto.net",
    "ulozto.sk",
    "ulozto.cz",
    "upload.ee",
    "uploadhaven.com",
    "up-4ever.com",
    "up-4ever.net",
    "uptobox.com",
    "uptobox.fr",
    "uptobox.eu",
    "uptobox.link",
    "uptostream.com",
    "uptostream.fr",
    "uptostream.eu",
    "uptostream.link",
    "upvid.pro",
    "upvid.live",
    "upvid.host",
    "upvid.biz",
    "upvid.cloud",
    "uqload.com",
    "uqload.co",
    "uqload.io",
    "userload.co",
    "usersdrive.com",
    "vidoza.net",
    "voe.sx",
    "voe-unblock.com",
    "voeunblock1.com",
    "voeunblock2.com",
    "voeunblock3.com",
    "voeunbl0ck.com",
    "voeunblck.com",
    "voeunblk.com",
    "voe-un-block.com",
    "voeun-block.net",
    "workupload.com",
    "world-bytez.com",
    "worldbytez.com",
    "world-files.com",
    "wupfile.com",
    "zippyshare.com",
]

real_debrid_supported_sites = [
    "1fichier.com",
    "2shared.com",
    "4shared.com",
    "alfafile.net",
    "anzfile.net",
    "backin.net",
    "bayfiles.com",
    "bdupload.in",
    "brupload.net",
    "btafile.com",
    "catshare.net",
    "clicknupload.me",
    "clipwatching.com",
    "cosmobox.org",
    "dailymotion.com",
    "dailyuploads.net",
    "daofile.com",
    "datafilehost.com",
    "ddownload.com",
    "depositfiles.com",
    "dl.free.fr",
    "douploads.net",
    "drop.download",
    "earn4files.com",
    "easybytez.com",
    "ex-load.com",
    "extmatrix.com",
    "down.fast-down.com",
    "fastclick.to",
    "faststore.org",
    "file.al",
    "file4safe.com",
    "fboom.me",
    "filefactory.com",
    "filefox.cc",
    "filenext.com",
    "filer.net",
    "filerio.in",
    "filesabc.com",
    "filespace.com",
    "file-up.org",
    "fileupload.pw",
    "filezip.cc",
    "fireget.com",
    "flashbit.cc",
    "flashx.tv",
    "florenfile.com",
    "fshare.vn",
    "gigapeta.com",
    "goloady.com",
    "docs.google.com",
    "gounlimited.to",
    "heroupload.com",
    "hexupload.net",
    "hitfile.net",
    "hotlink.cc",
    "hulkshare.com",
    "icerbox.com",
    "inclouddrive.com",
    "isra.cloud",
    "katfile.com",
    "keep2share.cc",
    "letsupload.cc",
    "load.to",
    "down.mdiaload.com",
    "mediafire.com",
    "mega.co.nz",
    "mixdrop.co",
    "mixloads.com",
    "mp4upload.com",
    "nelion.me",
    "ninjastream.to",
    "nitroflare.com",
    "nowvideo.club",
    "oboom.com",
    "prefiles.com",
    "rapidgator.net",
    "rapidrar.com",
    "rapidu.net",
    "rarefile.net",
    "real-debrid.com",
    "redbunker.net",
    "rockfile.eu",
    "rutube.ru",
    "scribd.com",
    "sendit.cloud",
    "sendspace.com",
    "simfileshare.net",
    "solidfiles.com",
    "soundcloud.com",
    "speed-down.org",
    "streamon.to",
    "streamtape.com",
    "takefile.link",
    "tezfiles.com",
    "thevideo.me",
    "turbobit.net",
    "tusfiles.com",
    "ubiqfile.com",
    "uloz.to",
    "unibytes.com",
    "uploadbox.io",
    "uploadboy.com",
    "uploadc.com",
    "uploaded.net",
    "uploadev.org",
    "uploadgig.com",
    "uploadrar.com",
    "uppit.com",
    "upstore.net",
    "upstream.to",
    "userscloud.com",
    "usersdrive.com",
    "vidcloud.ru",
    "videobin.co",
    "vidlox.tv",
    "vidoza.net",
    "vimeo.com",
    "vivo.sx",
    "vk.com",
    "voe.sx",
    "wdupload.com",
    "wipfiles.net",
    "world-files.com",
    "worldbytez.com",
    "wupfile.com",
    "wushare.com",
    "xubster.com",
]

GDFLIX_DOMAINS = ["gdflix.dev", "gdflix.io", "gdflix.lol", "gdflix.me"]

HUBCLOUD_DOMAINS = ["hubcloud.cx", "hubcloud.club", "hubcloud.fans", "hubcloud.one"]
HUBDRIVE_DOMAINS = ["hubdrive.tips", "hubdrive.in", "hubdrive.me"]
HUBCDN_DOMAINS = ["hubcdn.sbs", "hubcdn.in"]

# Anchor text fragments used to identify each HubCloud mirror server.
HUB_SERVER_LABELS = [
    ("FSLv2", ["fslv2"]),
    ("FSL", ["fsl server", "[fsl"]),
    ("10Gbps", ["10gbps", "10 gbps", "gpdl"]),
    ("Pixeldrain", ["pixel", "pixeldrain"]),
    ("Buzz", ["buzz", "bzzhr", "buzzheavier", "buzzserver"]),
    ("GoFile", ["gofile"]),
    ("Megaup", ["megaup"]),
    ("HubCDN", ["hubcdn"]),
]

HUB_SERVER_ORDER = [
    "FSLv2",
    "FSL",
    "10Gbps",
    "Pixeldrain",
    "Buzz",
    "GoFile",
    "Megaup",
    "HubCDN",
    "Direct",
]

# Ads, CDNs and navigation links that must never be treated as mirror servers.
HUB_SKIP_DOMAINS = [
    "hubcloud.cx/drive",
    "hubcloud.fans",
    "HDhub4u",
    "hdhub4u",
    "one.one.one",
    "tinyurl",
    "t.me",
    "google.com",
    "snvhost",
    "jquery",
    "jsdelivr",
    "fontawesome",
    "googleapis",
    "bootstrapcdn",
    "bonuscaf",
    "winexch",
]


def direct_link_generator(link):
    auth = None
    if isinstance(link, tuple):
        link, auth = link

    if is_magnet(link):
        if not Config.REAL_DEBRID_API:
            raise DirectDownloadLinkException(
                "ERROR: REAL_DEBRID_API is required to resolve magnet links here"
            )
        return real_debrid(link, True)

    domain = urlparse(link).hostname
    if not domain:
        raise DirectDownloadLinkException("ERROR: Invalid URL")
    elif "youtube.com" in domain or "youtu.be" in domain:
        raise DirectDownloadLinkException("ERROR: Use ytdl cmds for Youtube links")
    elif is_gdflix(link):
        return gdflix(link)
    elif is_hubcloud(link) or is_hubdrive(link) or is_hubcdn(link) or is_hblinks(link):
        return hubcloud(link)
    elif "tb-cdn.io" in domain or "torbox.app" in domain:
        return torbox(link)
    elif Config.DEBRID_LINK_API and any(
        x in domain for x in debrid_link_supported_sites
    ):
        return debrid_link(link)
    elif Config.REAL_DEBRID_API and any(
        x in domain for x in real_debrid_supported_sites
    ):
        return real_debrid(link)
    elif "yadi.sk" in link or "disk.yandex." in link:
        return yandex_disk(link)
    elif "buzzheavier.com" in domain:
        return buzzheavier(link)
    elif "devuploads" in domain:
        return devuploads(link)
    elif "lulacloud.com" in domain:
        return lulacloud(link)
    elif "fuckingfast.co" in domain:
        return fuckingfast_dl(link)
    elif "mediafire.com" in domain:
        return mediafire(link)
    elif "osdn.net" in domain:
        return osdn(link)
    elif "github.com" in domain:
        return github(link)
    elif "hxfile.co" in domain:
        return hxfile(link)
    elif "1drv.ms" in domain:
        return onedrive(link)
    elif "pixeldrain.com" in domain or "pixeldrain.dev" in domain:
        return pixeldrain(link)
    elif "racaty" in domain:
        return racaty(link)
    elif "1fichier.com" in domain:
        return fichier(link)
    elif "solidfiles.com" in domain:
        return solidfiles(link)
    elif "krakenfiles.com" in domain:
        return krakenfiles(link)
    elif "upload.ee" in domain:
        return uploadee(link)
    elif "gofile.io" in domain:
        return gofile(link, auth)
    elif "send.cm" in domain:
        return send_cm(link)
    elif "tmpsend.com" in domain:
        return tmpsend(link)
    elif "easyupload.io" in domain:
        return easyupload(link)
    elif "streamvid.net" in domain:
        return streamvid(link)
    elif "shrdsk.me" in domain:
        return shrdsk(link)
    elif "u.pcloud.link" in domain:
        return pcloud(link)
    elif "qiwi.gg" in domain:
        return qiwi(link)
    elif "mp4upload.com" in domain:
        return mp4upload(link)
    elif "berkasdrive.com" in domain:
        return berkasdrive(link)
    elif "swisstransfer.com" in domain:
        return swisstransfer(link)
    elif "instagram.com" in domain:
        return instagram(link)
    elif any(x in domain for x in ["akmfiles.com", "akmfls.xyz"]):
        return akmfiles(link)
    elif any(
        x in domain
        for x in [
            "dood.watch",
            "doodstream.com",
            "dood.to",
            "dood.so",
            "dood.cx",
            "dood.la",
            "dood.ws",
            "dood.sh",
            "doodstream.co",
            "dood.pm",
            "dood.wf",
            "dood.re",
            "dood.video",
            "dooood.com",
            "dood.yt",
            "doods.yt",
            "dood.stream",
            "doods.pro",
            "ds2play.com",
            "d0o0d.com",
            "ds2video.com",
            "do0od.com",
            "d000d.com",
        ]
    ):
        return doods(link)
    elif any(
        x in domain
        for x in [
            "streamtape.com",
            "streamtape.co",
            "streamtape.cc",
            "streamtape.to",
            "streamtape.net",
            "streamta.pe",
            "streamtape.xyz",
        ]
    ):
        return streamtape(link)
    elif any(x in domain for x in ["wetransfer.com", "we.tl"]):
        return wetransfer(link)
    elif any(
        x in domain
        for x in [
            "filelions.co",
            "filelions.site",
            "filelions.live",
            "filelions.to",
            "mycloudz.cc",
            "cabecabean.lol",
            "filelions.online",
            "embedwish.com",
            "kitabmarkaz.xyz",
            "wishfast.top",
            "streamwish.to",
            "kissmovies.net",
        ]
    ):
        return filelions_and_streamwish(link)
    elif any(x in domain for x in ["streamhub.ink", "streamhub.to"]):
        return streamhub(link)
    elif any(
        x in domain
        for x in [
            "linkbox.to",
            "lbx.to",
            "teltobx.net",
            "telbx.net",
        ]
    ):
        return linkBox(link)
    elif is_index_link(link) and link.endswith("/"):
        return gd_index(link, auth)
    elif is_share_link(link):
        if "gdtot" in domain:
            return gdtot(link)
        elif "filepress" in domain:
            return filepress(link)
        elif "jiodrive" in domain:
            return jiodrive(link)
        else:
            return sharer_scraper(link)
    elif "workers.dev" in domain:
        return mydrive_worker(link)
    elif any(
        x in domain
        for x in [
            "herokuapp.com",
            "vercel.app",
            "netlify.app",
            "railway.app",
            "render.com",
        ]
    ):
        return direct_stream_link(link)
    elif any(
        x in domain
        for x in [
            "anonfiles.com",
            "zippyshare.com",
            "letsupload.io",
            "hotfile.io",
            "bayfiles.com",
            "megaupload.nz",
            "letsupload.cc",
            "filechan.org",
            "myfile.is",
            "vshare.is",
            "rapidshare.nu",
            "lolabits.se",
            "openload.cc",
            "share-online.is",
            "upvid.cc",
            "uptobox.com",
            "uptobox.fr",
        ]
    ):
        raise DirectDownloadLinkException(f"ERROR: R.I.P {domain}")
    else:
        raise DirectDownloadLinkException(f"No Direct link function found for {link}")


def get_captcha_token(session, params):
    recaptcha_api = "https://www.google.com/recaptcha/api2"
    res = session.get(f"{recaptcha_api}/anchor", params=params)
    anchor_html = HTML(res.text)
    if not (anchor_token := anchor_html.xpath('//input[@id="recaptcha-token"]/@value')):
        return
    params["c"] = anchor_token[0]
    params["reason"] = "q"
    res = session.post(f"{recaptcha_api}/reload", params=params)
    if token := findall(r'"rresp","(.*?)"', res.text):
        return token[0]


def debrid_link(url):
    cget = create_scraper().request
    resp = cget(
        "POST",
        f"https://debrid-link.com/api/v2/downloader/add?access_token={Config.DEBRID_LINK_API}",
        data={"url": url},
    ).json()
    if resp["success"] != True:
        raise DirectDownloadLinkException(
            f"ERROR: {resp['error']} & ERROR ID: {resp['error_id']}"
        )
    if isinstance(resp["value"], dict):
        return resp["value"]["downloadUrl"]
    elif isinstance(resp["value"], list):
        details = {
            "contents": [],
            "title": unquote(url.rstrip("/").split("/")[-1]),
            "total_size": 0,
        }
        for dl in resp["value"]:
            if dl.get("expired", False):
                continue
            item = {
                "path": ospath.join(details["title"]),
                "filename": dl["name"],
                "url": dl["downloadUrl"],
            }
            if "size" in dl:
                details["total_size"] += dl["size"]
            details["contents"].append(item)
        return details


def real_debrid(url: str, tor=False):
    """Real-Debrid unrestrict/magnet resolver."""

    def __unrestrict(link, as_tuple=False):
        cget = create_scraper().request
        resp = cget(
            "POST",
            f"https://api.real-debrid.com/rest/1.0/unrestrict/link?auth_token={Config.REAL_DEBRID_API}",
            data={"link": link},
        )
        if resp.status_code != 200:
            raise DirectDownloadLinkException(f"ERROR: {resp.json().get('error')}")
        _res = resp.json()
        if as_tuple:
            return _res["filename"], _res["download"]
        return _res["download"]

    def __addMagnet(magnet):
        cget = create_scraper().request
        hash_ = search(r"(?<=xt=urn:btih:)[a-zA-Z0-9]+", magnet)
        if not hash_:
            raise DirectDownloadLinkException("ERROR: Unable to parse magnet hash")
        hash_ = hash_.group(0)
        resp = cget(
            "GET",
            f"https://api.real-debrid.com/rest/1.0/torrents/instantAvailability/{hash_}?auth_token={Config.REAL_DEBRID_API}",
        )
        if resp.status_code != 200 or not resp.json().get(hash_.lower(), {}).get("rd"):
            raise DirectDownloadLinkException(
                "ERROR: This magnet is not cached on Real-Debrid"
            )
        resp = cget(
            "POST",
            f"https://api.real-debrid.com/rest/1.0/torrents/addMagnet?auth_token={Config.REAL_DEBRID_API}",
            data={"magnet": magnet},
        )
        if resp.status_code != 201:
            raise DirectDownloadLinkException(f"ERROR: {resp.json().get('error')}")
        _id = resp.json()["id"]
        _file = cget(
            "POST",
            f"https://api.real-debrid.com/rest/1.0/torrents/selectFiles/{_id}?auth_token={Config.REAL_DEBRID_API}",
            data={"files": "all"},
        )
        if _file.status_code != 204:
            raise DirectDownloadLinkException(f"ERROR: {_file.json().get('error')}")

        contents = {"links": []}
        for _ in range(60):
            _res = cget(
                "GET",
                f"https://api.real-debrid.com/rest/1.0/torrents/info/{_id}?auth_token={Config.REAL_DEBRID_API}",
            )
            if _res.status_code != 200:
                raise DirectDownloadLinkException(f"ERROR: {_res.json().get('error')}")
            contents = _res.json()
            if contents.get("links"):
                break
            sleep(1)
        if not contents.get("links"):
            raise DirectDownloadLinkException(
                "ERROR: Real-Debrid did not return any links for this magnet"
            )

        details = {
            "contents": [],
            "title": contents["original_filename"],
            "total_size": contents["bytes"],
        }
        for file_info, link in zip(contents["files"], contents["links"]):
            filename, dl_url = __unrestrict(link, as_tuple=True)
            details["contents"].append(
                {
                    "path": ospath.join(
                        details["title"],
                        ospath.dirname(file_info["path"]).lstrip("/"),
                    ),
                    "filename": unquote(filename),
                    "url": dl_url,
                }
            )
        return details

    if not Config.REAL_DEBRID_API:
        raise DirectDownloadLinkException("ERROR: REAL_DEBRID_API is not provided")
    try:
        if not tor:
            return __unrestrict(url)
        details = __addMagnet(url)
    except DirectDownloadLinkException:
        raise
    except Exception as e:
        raise DirectDownloadLinkException(f"ERROR: {e}") from e
    if len(details["contents"]) == 1:
        return details["contents"][0]["url"]
    return details


def buzzheavier(link):
    link = link if link.endswith("/") else link + "/"
    client = create_scraper()
    try:
        res = client.get(
            link + "download", headers={"hx-current-url": link, "referer": link}
        )
    except Exception as e:
        raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e

    domain = urlparse(link).netloc
    redirect_url = res.headers.get("Hx-Redirect", "None")

    if redirect_url == "None":
        raise DirectDownloadLinkException("ERROR: Direct link not found")

    if not redirect_url.startswith("http"):
        return f"https://{domain}{redirect_url}"
    return redirect_url


def fuckingfast_dl(url):
    session = Session()
    url = url.strip()

    try:
        response = session.get(url)
        content = response.text
        pattern = r'window\.open\((["\'])(https://fuckingfast\.co/dl/[^"\']+)\1'
        match = search(pattern, content)

        if not match:
            raise DirectDownloadLinkException(
                "ERROR: Could not find download link in page"
            )

        direct_url = match.group(2)
        return direct_url

    except Exception as e:
        raise DirectDownloadLinkException(f"ERROR: {str(e)}") from e
    finally:
        session.close()


def devuploads(url):
    session = Session()
    res = session.get(url)
    html = HTML(res.text)
    if not html.xpath("//input[@name]"):
        raise DirectDownloadLinkException("ERROR: Unable to find link data")
    data = {i.get("name"): i.get("value") for i in html.xpath("//input[@name]")}
    res = session.post("https://gujjukhabar.in/", data=data)
    html = HTML(res.text)
    if not html.xpath("//input[@name]"):
        raise DirectDownloadLinkException("ERROR: Unable to find link data")
    data = {i.get("name"): i.get("value") for i in html.xpath("//input[@name]")}
    resp = session.get(
        "https://du2.devuploads.com/dlhash.php",
        headers={
            "Origin": "https://gujjukhabar.in",
            "Referer": "https://gujjukhabar.in/",
        },
    )
    if not resp.text:
        raise DirectDownloadLinkException("ERROR: Unable to find ipp value")
    data["ipp"] = resp.text.strip()
    if not data.get("rand"):
        raise DirectDownloadLinkException("ERROR: Unable to find rand value")
    randpost = session.post(
        "https://devuploads.com/token/token.php",
        data={"rand": data["rand"], "msg": ""},
        headers={
            "Origin": "https://gujjukhabar.in",
            "Referer": "https://gujjukhabar.in/",
        },
    )
    if not randpost:
        raise DirectDownloadLinkException("ERROR: Unable to find xd value")
    data["xd"] = randpost.text.strip()
    # Optional proxy via GUJJU_PROXY_URL env (never hard-code credentials).
    proxy_env = (_os.environ.get("GUJJU_PROXY_URL") or "").strip()
    request_kwargs = {"data": data}
    if proxy_env:
        request_kwargs["proxies"] = {"http": proxy_env, "https": proxy_env}
    res = session.post(url, **request_kwargs)
    html = HTML(res.text)
    if not html.xpath("//input[@name='orilink']/@value"):
        raise DirectDownloadLinkException("ERROR: Unable to find Direct Link")
    direct_link = html.xpath("//input[@name='orilink']/@value")
    session.close()
    return direct_link[0]


def lulacloud(url):
    session = Session()
    try:
        res = session.post(url, headers={"Referer": url}, allow_redirects=False)
        return res.headers["location"]
    except Exception as e:
        raise DirectDownloadLinkException(f"ERROR: {str(e)}") from e
    finally:
        session.close()


def mediafire(url, session=None):
    if "/folder/" in url:
        return mediafireFolder(url)
    if "::" in url:
        _password = url.split("::")[-1]
        url = url.split("::")[-2]
    else:
        _password = ""
    if final_link := findall(
        r"https?:\/\/download\d+\.mediafire\.com\/\S+\/\S+\/\S+", url
    ):
        return final_link[0]

    def _repair_download(url, session):
        try:
            html = HTML(session.get(url).text)
            if new_link := html.xpath('//a[@id="continue-btn"]/@href'):
                return mediafire(f"https://mediafire.com/{new_link[0]}")
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e

    if session is None:
        session = create_scraper()
        parsed_url = urlparse(url)
        url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
    try:
        html = HTML(session.get(url).text)
    except Exception as e:
        session.close()
        raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
    if error := html.xpath('//p[@class="notranslate"]/text()'):
        session.close()
        raise DirectDownloadLinkException(f"ERROR: {error[0]}")
    if html.xpath("//div[@class='passwordPrompt']"):
        if not _password:
            session.close()
            raise DirectDownloadLinkException(
                f"ERROR: {PASSWORD_ERROR_MESSAGE}".format(url)
            )
        try:
            html = HTML(session.post(url, data={"downloadp": _password}).text)
        except Exception as e:
            session.close()
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
        if html.xpath("//div[@class='passwordPrompt']"):
            session.close()
            raise DirectDownloadLinkException("ERROR: Wrong password.")
    if not (final_link := html.xpath('//a[@aria-label="Download file"]/@href')):
        if repair_link := html.xpath("//a[@class='retry']/@href"):
            return _repair_download(repair_link[0], session)
        raise DirectDownloadLinkException(
            "ERROR: No links found in this page Try Again"
        )
    if final_link[0].startswith("//"):
        final_url = f"https://{final_link[0][2:]}"
        if _password:
            final_url += f"::{_password}"
        return mediafire(final_url, session)
    session.close()
    return final_link[0]


def osdn(url):
    with create_scraper() as session:
        try:
            html = HTML(session.get(url).text)
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
        if not (direct_link := html.xpath('//a[@class="mirror_link"]/@href')):
            raise DirectDownloadLinkException("ERROR: Direct link not found")
        return f"https://osdn.net{direct_link[0]}"


def yandex_disk(url: str) -> str:
    # Based on https://github.com/wldhx/yadisk-direct
    try:
        link = findall(r"\b(https?://(yadi\.sk|disk\.yandex\.(com|ru))\S+)", url)[0][0]
    except IndexError:
        return "No Yandex.Disk links found\n"
    api = "https://cloud-api.yandex.net/v1/disk/public/resources/download?public_key={}"
    try:
        return get(api.format(link)).json()["href"]
    except KeyError as e:
        raise DirectDownloadLinkException(
            "ERROR: File not found/Download limit reached"
        ) from e


def github(url):
    try:
        findall(r"\bhttps?://.*github\.com.*releases\S+", url)[0]
    except IndexError as e:
        raise DirectDownloadLinkException("No GitHub Releases links found") from e
    with create_scraper() as session:
        _res = session.get(url, stream=True, allow_redirects=False)
        if "location" in _res.headers:
            return _res.headers["location"]
        raise DirectDownloadLinkException("ERROR: Can't extract the link")


def hxfile(url):
    if not ospath.isfile("hxfile.txt"):
        raise DirectDownloadLinkException("ERROR: hxfile.txt (cookies) Not Found!")
    try:
        jar = MozillaCookieJar()
        jar.load("hxfile.txt")
    except Exception as e:
        raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
    cookies = {cookie.name: cookie.value for cookie in jar}
    with Session() as session:
        try:
            if url.strip().endswith(".html"):
                url = url[:-5]
            file_code = url.split("/")[-1]
            html = HTML(
                session.post(
                    url,
                    data={"op": "download2", "id": file_code},
                    cookies=cookies,
                ).text
            )
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
    if direct_link := html.xpath("//a[@class='btn btn-dow']/@href"):
        header = f"Referer: {url}"
        return direct_link[0], header
    raise DirectDownloadLinkException("ERROR: Direct download link not found")


def onedrive(link):
    # By https://github.com/junedkh
    with create_scraper() as session:
        try:
            link = session.get(link).url
            parsed_link = urlparse(link)
            link_data = parse_qs(parsed_link.query)
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
        if not link_data:
            raise DirectDownloadLinkException("ERROR: Unable to find link_data")
        folder_id = link_data.get("resid")
        if not folder_id:
            raise DirectDownloadLinkException("ERROR: folder id not found")
        folder_id = folder_id[0]
        authkey = link_data.get("authkey")
        if not authkey:
            raise DirectDownloadLinkException("ERROR: authkey not found")
        authkey = authkey[0]
        boundary = uuid4()
        headers = {"content-type": f"multipart/form-data;boundary={boundary}"}
        data = f"--{boundary}\r\nContent-Disposition: form-data;name=data\r\nPrefer: Migration=EnableRedirect;FailOnMigratedFiles\r\nX-HTTP-Method-Override: GET\r\nContent-Type: application/json\r\n\r\n--{boundary}--"
        try:
            resp = session.get(
                f"https://api.onedrive.com/v1.0/drives/{folder_id.split('!', 1)[0]}/items/{folder_id}?$select=id,@content.downloadUrl&ump=1&authKey={authkey}",
                headers=headers,
                data=data,
            ).json()
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
    if "@content.downloadUrl" not in resp:
        raise DirectDownloadLinkException("ERROR: Direct link not found")
    return resp["@content.downloadUrl"]


def pixeldrain(url):
    url = url.strip("/ ")
    parts = url.split("/")
    file_id = parts[-1].split("?", 1)[0]
    path_segment = parts[-2] if len(parts) >= 2 else ""

    # /l/ is a file list (folder); /f/ and /u/ are single files.
    if path_segment in ("l", "list"):
        api_info_url = f"https://pixeldrain.com/api/list/{file_id}"
        download_url = f"https://pixeldrain.com/api/list/{file_id}/zip?download"
    else:
        api_info_url = f"https://pixeldrain.com/api/file/{file_id}/info"
        download_url = f"https://pixeldrain.com/api/file/{file_id}?download"

    with create_scraper() as session:
        try:
            resp = session.get(api_info_url).json()
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e

    if resp.get("success"):
        return download_url
    raise DirectDownloadLinkException(
        f"ERROR: Can't download due {resp.get('message', 'unknown error')}."
    )


def streamtape(url):
    splitted_url = url.split("/")
    _id = splitted_url[4] if len(splitted_url) >= 6 else splitted_url[-1]
    try:
        with Session() as session:
            html = HTML(session.get(url).text)
    except Exception as e:
        raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
    script = html.xpath(
        "//script[contains(text(),'ideoooolink')]/text()"
    ) or html.xpath("//script[contains(text(),'ideoolink')]/text()")
    if not script:
        raise DirectDownloadLinkException("ERROR: requeries script not found")
    if not (link := findall(r"(&expires\S+)'", script[0])):
        raise DirectDownloadLinkException("ERROR: Download link not found")
    return f"https://streamtape.com/get_video?id={_id}{link[-1]}"


def racaty(url):
    with create_scraper() as session:
        try:
            url = session.get(url).url
            json_data = {"op": "download2", "id": url.split("/")[-1]}
            html = HTML(session.post(url, data=json_data).text)
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
    if direct_link := html.xpath("//a[@id='uniqueExpirylink']/@href"):
        return direct_link[0]
    else:
        raise DirectDownloadLinkException("ERROR: Direct link not found")


def fichier(link):
    # Based on https://github.com/Maujar
    regex = r"^([http:\/\/|https:\/\/]+)?.*1fichier\.com\/\?.+"
    gan = match(regex, link)
    if not gan:
        raise DirectDownloadLinkException("ERROR: The link you entered is wrong!")
    if "::" in link:
        pswd = link.split("::")[-1]
        url = link.split("::")[-2]
    else:
        pswd = None
        url = link
    cget = create_scraper().request
    try:
        if pswd is None:
            req = cget("post", url)
        else:
            pw = {"pass": pswd}
            req = cget("post", url, data=pw)
    except Exception as e:
        raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
    if req.status_code == 404:
        raise DirectDownloadLinkException(
            "ERROR: File not found/The link you entered is wrong!"
        )
    html = HTML(req.text)
    if dl_url := html.xpath('//a[@class="ok btn-general btn-orange"]/@href'):
        return dl_url[0]
    if not (ct_warn := html.xpath('//div[@class="ct_warn"]')):
        raise DirectDownloadLinkException(
            "ERROR: Error trying to generate Direct Link from 1fichier!"
        )
    if len(ct_warn) == 3:
        str_2 = ct_warn[-1].text
        if "you must wait" in str_2.lower():
            if numbers := [int(word) for word in str_2.split() if word.isdigit()]:
                raise DirectDownloadLinkException(
                    f"ERROR: 1fichier is on a limit. Please wait {numbers[0]} minute."
                )
            else:
                raise DirectDownloadLinkException(
                    "ERROR: 1fichier is on a limit. Please wait a few minutes/hour."
                )
        elif "protect access" in str_2.lower():
            raise DirectDownloadLinkException(
                f"ERROR:\n{PASSWORD_ERROR_MESSAGE.format(link)}"
            )
        else:
            raise DirectDownloadLinkException(
                "ERROR: Failed to generate Direct Link from 1fichier!"
            )
    elif len(ct_warn) == 4:
        str_1 = ct_warn[-2].text
        str_3 = ct_warn[-1].text
        if "you must wait" in str_1.lower():
            if numbers := [int(word) for word in str_1.split() if word.isdigit()]:
                raise DirectDownloadLinkException(
                    f"ERROR: 1fichier is on a limit. Please wait {numbers[0]} minute."
                )
            else:
                raise DirectDownloadLinkException(
                    "ERROR: 1fichier is on a limit. Please wait a few minutes/hour."
                )
        elif "bad password" in str_3.lower():
            raise DirectDownloadLinkException(
                "ERROR: The password you entered is wrong!"
            )
    raise DirectDownloadLinkException(
        "ERROR: Error trying to generate Direct Link from 1fichier!"
    )


def solidfiles(url):
    # Based on https://github.com/Xonshiz/SolidFiles-Downloader; by https://github.com/Jusidama18
    with create_scraper() as session:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36"
            }
            pageSource = session.get(url, headers=headers).text
            mainOptions = str(
                search(r"viewerOptions\'\,\ (.*?)\)\;", pageSource).group(1)
            )
            return loads(mainOptions)["downloadUrl"]
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e


def krakenfiles(url):
    with Session() as session:
        try:
            _res = session.get(url)
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
        html = HTML(_res.text)
        if post_url := html.xpath('//form[@id="dl-form"]/@action'):
            post_url = f"https://krakenfiles.com{post_url[0]}"
        else:
            raise DirectDownloadLinkException("ERROR: Unable to find post link.")
        if token := html.xpath('//input[@id="dl-token"]/@value'):
            data = {"token": token[0]}
        else:
            raise DirectDownloadLinkException("ERROR: Unable to find token for post.")
        try:
            _json = session.post(post_url, data=data).json()
        except Exception as e:
            raise DirectDownloadLinkException(
                f"ERROR: {e.__class__.__name__} While send post request"
            ) from e
    if _json["status"] != "ok":
        raise DirectDownloadLinkException(
            "ERROR: Unable to find download after post request"
        )
    return _json["url"]


def uploadee(url):
    with create_scraper() as session:
        try:
            html = HTML(session.get(url).text)
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
    if link := html.xpath("//a[@id='d_l']/@href"):
        return link[0]
    else:
        raise DirectDownloadLinkException("ERROR: Direct Link not found")


def filepress(url):
    with create_scraper() as session:
        try:
            url = session.get(url).url
            raw = urlparse(url)
            json_data = {
                "id": raw.path.split("/")[-1],
                "method": "publicDownlaod",
            }
            api = f"{raw.scheme}://{raw.hostname}/api/file/downlaod/"
            res2 = session.post(
                api,
                headers={"Referer": f"{raw.scheme}://{raw.hostname}"},
                json=json_data,
            ).json()
            json_data2 = {
                "id": res2["data"],
                "method": "publicUserDownlaod",
            }
            api2 = "https://new2.filepress.store/api/file/downlaod2/"
            res = session.post(
                api2,
                headers={"Referer": f"{raw.scheme}://{raw.hostname}"},
                json=json_data2,
            ).json()
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
    if "data" not in res:
        raise DirectDownloadLinkException(f"ERROR: {res['statusText']}")
    return f"https://drive.google.com/uc?id={res['data']}&export=download"


def jiodrive(url):
    if not Config.JIODRIVE_TOKEN:
        raise DirectDownloadLinkException("ERROR: JIODRIVE_TOKEN is not provided")
    with create_scraper() as session:
        try:
            url = session.get(url).url
            resp = session.post(
                "https://www.jiodrive.xyz/ajax.php?ajax=download",
                cookies={"access_token": Config.JIODRIVE_TOKEN},
                data={"id": url.split("/")[-1]},
            ).json()
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
    if resp.get("code") != "200":
        raise DirectDownloadLinkException(
            "ERROR: The user's Drive storage quota has been exceeded."
        )
    return resp["file"]


def gd_index(url, auth=None):
    """Bhadoo-style Google Drive index (``/0:/``) folder walker."""
    if not auth:
        auth = ("admin", "admin")
    username, password = auth[0], auth[1]

    # The last path segment is the folder name, except for a drive root
    # ("/0:/") where it carries no meaning — fall back to the host there.
    segments = [s for s in urlparse(url).path.split("/") if s]
    title = segments[-1] if segments else ""
    if not title or match(r"^\d+:$", title):
        title = urlparse(url).hostname or "index"

    details = {
        "contents": [],
        "title": unquote(title),
        "total_size": 0,
    }

    def __fetch_links(_url, folderPath):
        with create_scraper() as session:
            payload = {
                "id": "",
                "type": "folder",
                "username": username,
                "password": password,
                "page_token": "",
                "page_index": 0,
            }
            try:
                data = session.post(_url, json=payload).json()
            except Exception as e:
                raise DirectDownloadLinkException(
                    "ERROR: Use a latest Bhadoo Index link"
                ) from e
        for file_info in data.get("data", {}).get("files", []):
            if file_info.get("mimeType") == "application/vnd.google-apps.folder":
                newFolderPath = ospath.join(
                    folderPath or details["title"], file_info["name"]
                )
                __fetch_links(f"{_url}{file_info['name']}/", newFolderPath)
            else:
                if not folderPath:
                    folderPath = details["title"]
                details["contents"].append(
                    {
                        "path": ospath.join(folderPath),
                        "filename": unquote(file_info["name"]),
                        "url": urljoin(_url, file_info.get("link") or ""),
                    }
                )
                if "size" in file_info:
                    details["total_size"] += int(file_info["size"])

    try:
        __fetch_links(url, "")
    except DirectDownloadLinkException:
        raise
    except Exception as e:
        raise DirectDownloadLinkException(f"ERROR: {e}") from e
    if not details["contents"]:
        raise DirectDownloadLinkException("ERROR: No files found in this index link")
    if len(details["contents"]) == 1:
        return details["contents"][0]["url"]
    return details


def mydrive_worker(url):
    """Cloudflare Worker Drive mirrors expose the real name via Content-Disposition."""
    req_headers = {"User-Agent": user_agent}
    content_disposition = ""

    try:
        with Session() as s:
            resp = s.head(url, headers=req_headers, timeout=10, allow_redirects=True)
            content_disposition = resp.headers.get("Content-Disposition", "")
    except Exception:
        pass  # Some workers reject HEAD; fall through to the GET probe.

    if not content_disposition:
        try:
            with Session() as s:
                resp = s.get(
                    url,
                    headers=req_headers,
                    timeout=10,
                    allow_redirects=True,
                    stream=True,
                )
                content_disposition = resp.headers.get("Content-Disposition", "")
                resp.close()
        except Exception as e:
            raise DirectDownloadLinkException(
                f"ERROR: mydrive_worker - {e.__class__.__name__}: {e}"
            ) from e

    filename = __parse_content_disposition(content_disposition)
    if not filename:
        raise DirectDownloadLinkException(
            "ERROR: mydrive_worker - Could not determine filename. "
            "The server did not return a Content-Disposition header."
        )

    LOGGER.info(f"mydrive_worker: resolved filename -> {filename}")
    return {
        "contents": [{"path": "", "filename": filename, "url": url}],
        "title": filename,
        "total_size": 0,
    }


def torbox(url: str):
    filename = __get_filename_from_headers(url)
    if not filename:
        filename = url.split("/")[-1].split("?")[0]
        if "/zip/" in url and not filename.endswith(".zip"):
            filename += ".zip"
    if not filename:
        raise DirectDownloadLinkException("ERROR: Unable to determine TorBox filename")
    return {
        "contents": [{"path": "", "filename": filename, "url": url}],
        "title": filename,
        "total_size": 0,
    }


def direct_stream_link(url):
    """Pass-through for hosts that already serve the file directly."""
    try:
        with create_scraper() as session:
            resp = session.head(url, allow_redirects=True)
            if resp.status_code != 200:
                raise DirectDownloadLinkException(
                    f"ERROR: Link not accessible (Status: {resp.status_code})"
                )
            filename = __parse_content_disposition(
                resp.headers.get("Content-Disposition", "")
            )
    except DirectDownloadLinkException:
        raise
    except Exception as e:
        raise DirectDownloadLinkException(
            f"ERROR: {e.__class__.__name__} - {e}"
        ) from e

    if not filename:
        filename = unquote(urlparse(url).path.split("/")[-1].split("?")[0])
    if not filename:
        raise DirectDownloadLinkException("ERROR: Unable to determine filename")
    return {
        "contents": [{"path": "", "filename": filename, "url": url}],
        "title": filename,
        "total_size": 0,
    }


def __parse_content_disposition(content_disposition):
    """Extract a filename from a Content-Disposition header value."""
    if not content_disposition:
        return None
    # RFC 5987 form takes precedence: filename*=UTF-8''Dark%20S01.zip
    if "filename*=" in content_disposition:
        try:
            part = (
                content_disposition.split("filename*=")[1]
                .split(";")[0]
                .strip()
                .strip("\"'")
            )
            if "''" in part:
                part = part.split("''")[1]
            if filename := unquote(part):
                return filename
        except Exception:
            pass
    if "filename=" in content_disposition:
        try:
            part = (
                content_disposition.split("filename=")[1]
                .split(";")[0]
                .strip()
                .strip("\"'")
            )
            if filename := unquote(part):
                return filename
        except Exception:
            pass
    return None


def __get_filename_from_headers(url, headers=None):
    """Probe a URL's headers for its real filename without downloading the body."""
    try:
        response = get(
            url,
            headers=headers or {"User-Agent": user_agent},
            timeout=10,
            allow_redirects=True,
            stream=True,
        )
        response.raise_for_status()
        filename = __parse_content_disposition(
            response.headers.get("Content-Disposition", "")
        )
        response.close()
        return filename
    except Exception as e:
        LOGGER.debug(f"Failed to fetch filename from headers: {e}")
        return None


def gdtot(url):
    cget = create_scraper().request
    try:
        res = cget("GET", f"https://gdtot.pro/file/{url.split('/')[-1]}")
    except Exception as e:
        raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
    token_url = HTML(res.text).xpath(
        "//a[contains(@class,'inline-flex items-center justify-center')]/@href"
    )
    if not token_url:
        try:
            url = cget("GET", url).url
            p_url = urlparse(url)
            res = cget(
                "GET", f"{p_url.scheme}://{p_url.hostname}/ddl/{url.split('/')[-1]}"
            )
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
        if (
            drive_link := findall(r"myDl\('(.*?)'\)", res.text)
        ) and "drive.google.com" in drive_link[0]:
            return drive_link[0]
        else:
            raise DirectDownloadLinkException(
                "ERROR: Drive Link not found, Try in your broswer"
            )
    token_url = token_url[0]
    try:
        token_page = cget("GET", token_url)
    except Exception as e:
        raise DirectDownloadLinkException(
            f"ERROR: {e.__class__.__name__} with {token_url}"
        ) from e
    path = findall(r'\("(.*?)"\)', token_page.text)
    if not path:
        raise DirectDownloadLinkException("ERROR: Cannot bypass this")
    path = path[0]
    raw = urlparse(token_url)
    final_url = f"{raw.scheme}://{raw.hostname}{path}"
    return sharer_scraper(final_url)


def sharer_scraper(url):
    cget = create_scraper().request
    try:
        url = cget("GET", url).url
        raw = urlparse(url)
        header = {
            "useragent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/7.0.548.0 Safari/534.10"
        }
        res = cget("GET", url, headers=header)
    except Exception as e:
        raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
    key = findall(r'"key",\s+"(.*?)"', res.text)
    if not key:
        raise DirectDownloadLinkException("ERROR: Key not found!")
    key = key[0]
    if not HTML(res.text).xpath("//button[@id='drc']"):
        raise DirectDownloadLinkException(
            "ERROR: This link don't have direct download button"
        )
    boundary = uuid4()
    headers = {
        "Content-Type": f"multipart/form-data; boundary=----WebKitFormBoundary{boundary}",
        "x-token": raw.hostname,
        "useragent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/7.0.548.0 Safari/534.10",
    }

    data = (
        f'------WebKitFormBoundary{boundary}\r\nContent-Disposition: form-data; name="action"\r\n\r\ndirect\r\n'
        f'------WebKitFormBoundary{boundary}\r\nContent-Disposition: form-data; name="key"\r\n\r\n{key}\r\n'
        f'------WebKitFormBoundary{boundary}\r\nContent-Disposition: form-data; name="action_token"\r\n\r\n\r\n'
        f"------WebKitFormBoundary{boundary}--\r\n"
    )
    try:
        res = cget("POST", url, cookies=res.cookies, headers=headers, data=data).json()
    except Exception as e:
        raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
    if "url" not in res:
        raise DirectDownloadLinkException(
            "ERROR: Drive Link not found, Try in your broswer"
        )
    if "drive.google.com" in res["url"] or "drive.usercontent.google.com" in res["url"]:
        return res["url"]
    try:
        res = cget("GET", res["url"])
    except Exception as e:
        raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
    if (drive_link := HTML(res.text).xpath("//a[contains(@class,'btn')]/@href")) and (
        "drive.google.com" in drive_link[0]
        or "drive.usercontent.google.com" in drive_link[0]
    ):
        return drive_link[0]
    else:
        raise DirectDownloadLinkException(
            "ERROR: Drive Link not found, Try in your broswer"
        )


def wetransfer(url):
    with create_scraper() as session:
        try:
            url = session.get(url).url
            splited_url = url.split("/")
            json_data = {"security_hash": splited_url[-1], "intent": "entire_transfer"}
            res = session.post(
                f"https://wetransfer.com/api/v4/transfers/{splited_url[-2]}/download",
                json=json_data,
            ).json()
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
    if "direct_link" in res:
        return res["direct_link"]
    elif "message" in res:
        raise DirectDownloadLinkException(f"ERROR: {res['message']}")
    elif "error" in res:
        raise DirectDownloadLinkException(f"ERROR: {res['error']}")
    else:
        raise DirectDownloadLinkException("ERROR: cannot find direct link")


def akmfiles(url):
    with create_scraper() as session:
        try:
            html = HTML(
                session.post(
                    url,
                    data={"op": "download2", "id": url.split("/")[-1]},
                ).text
            )
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
    if direct_link := html.xpath("//a[contains(@class,'btn btn-dow')]/@href"):
        return direct_link[0]
    else:
        raise DirectDownloadLinkException("ERROR: Direct link not found")


def shrdsk(url):
    with create_scraper() as session:
        try:
            _json = session.get(
                f"https://us-central1-affiliate2apk.cloudfunctions.net/get_data?shortid={url.split('/')[-1]}",
            ).json()
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
        if "download_data" not in _json:
            raise DirectDownloadLinkException("ERROR: Download data not found")
        try:
            _res = session.get(
                f"https://shrdsk.me/download/{_json['download_data']}",
                allow_redirects=False,
            )
            if "Location" in _res.headers:
                return _res.headers["Location"]
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
    raise DirectDownloadLinkException("ERROR: cannot find direct link in headers")


def linkBox(url: str):
    parsed_url = urlparse(url)
    try:
        shareToken = parsed_url.path.split("/")[-1]
    except Exception:
        raise DirectDownloadLinkException("ERROR: invalid URL")

    details = {"contents": [], "title": "", "total_size": 0}

    def __singleItem(session, itemId):
        try:
            _json = session.get(
                "https://www.linkbox.to/api/file/detail",
                params={"itemId": itemId},
            ).json()
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
        data = _json["data"]
        if not data:
            if "msg" in _json:
                raise DirectDownloadLinkException(f"ERROR: {_json['msg']}")
            raise DirectDownloadLinkException("ERROR: data not found")
        itemInfo = data["itemInfo"]
        if not itemInfo:
            raise DirectDownloadLinkException("ERROR: itemInfo not found")
        filename = itemInfo["name"]
        sub_type = itemInfo.get("sub_type")
        if sub_type and not filename.strip().endswith(sub_type):
            filename += f".{sub_type}"
        if not details["title"]:
            details["title"] = filename
        item = {
            "path": "",
            "filename": filename,
            "url": itemInfo["url"],
        }
        if "size" in itemInfo:
            size = itemInfo["size"]
            if isinstance(size, str) and size.isdigit():
                size = float(size)
            details["total_size"] += size
        details["contents"].append(item)

    def __fetch_links(session, _id=0, folderPath=""):
        params = {
            "shareToken": shareToken,
            "pageSize": 1000,
            "pid": _id,
        }
        try:
            _json = session.get(
                "https://www.linkbox.to/api/file/share_out_list",
                params=params,
            ).json()
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
        data = _json["data"]
        if not data:
            if "msg" in _json:
                raise DirectDownloadLinkException(f"ERROR: {_json['msg']}")
            raise DirectDownloadLinkException("ERROR: data not found")
        try:
            if data["shareType"] == "singleItem":
                return __singleItem(session, data["itemId"])
        except Exception:
            pass
        if not details["title"]:
            details["title"] = data["dirName"]
        contents = data["list"]
        if not contents:
            return
        for content in contents:
            if content["type"] == "dir" and "url" not in content:
                if not folderPath:
                    newFolderPath = ospath.join(details["title"], content["name"])
                else:
                    newFolderPath = ospath.join(folderPath, content["name"])
                if not details["title"]:
                    details["title"] = content["name"]
                __fetch_links(session, content["id"], newFolderPath)
            elif "url" in content:
                if not folderPath:
                    folderPath = details["title"]
                filename = content["name"]
                if (
                    sub_type := content.get("sub_type")
                ) and not filename.strip().endswith(sub_type):
                    filename += f".{sub_type}"
                item = {
                    "path": ospath.join(folderPath),
                    "filename": filename,
                    "url": content["url"],
                }
                if "size" in content:
                    size = content["size"]
                    if isinstance(size, str) and size.isdigit():
                        size = float(size)
                    details["total_size"] += size
                details["contents"].append(item)

    try:
        with Session() as session:
            __fetch_links(session)
    except DirectDownloadLinkException as e:
        raise e
    return details


@lru_cache(1)
def _gofile_salt(_slot):
    """Recover GoFile's website-token salt from their obfuscated wt.obf.js.

    The salt is an RC4-encrypted 14-hex-char string hidden in a string table;
    ``_slot`` only exists to bust the cache when the 4-hour time slot rolls over.
    """
    try:
        js = get("https://gofile.io/js/wt.obf.js", timeout=15).text
        js = sub(r"\\x([0-9a-f]{2})", lambda m: chr(int(m[1], 16)), js)
        strings = findall(r"'([^']*)'", search(r"\[((?:'[^']*',?)+)\]", js)[1])
        keys = set(findall(r",'([^']{4})'\)", js))
        for raw in (b64decode(x.swapcase() + "===") for x in strings):
            for key in keys:
                box, j = list(range(256)), 0
                for i in range(256):
                    j = (j + box[i] + ord(key[i % 4])) % 256
                    box[i], box[j] = box[j], box[i]
                i = j = 0
                out = bytearray()
                for c in raw:
                    i = (i + 1) % 256
                    j = (j + box[i]) % 256
                    box[i], box[j] = box[j], box[i]
                    out.append(c ^ box[(box[i] + box[j]) % 256])
                if fullmatch(rb"[0-9a-f]{14}", out):
                    return out.decode()
    except Exception as e:
        LOGGER.debug(f"GoFile salt extraction failed: {e}")
    return "12af056dacea0b"


def gofile(url, auth=None):
    try:
        if auth and len(auth) > 1 and auth[1]:
            _password = sha256(auth[1].encode("utf-8")).hexdigest()
        elif "::" in url:
            _password = sha256(url.split("::")[-1].encode("utf-8")).hexdigest()
            url = url.split("::")[-2]
        else:
            _password = ""
        _id = url.split("/")[-1]
    except Exception as e:
        raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")

    def __build_headers(active_token):
        time_slot = int(time()) // 14400
        raw = (
            f"{user_agent}::en-US::{active_token}::{time_slot}::"
            f"{_gofile_salt(time_slot)}"
        )
        return {
            "User-Agent": user_agent,
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "*/*",
            "Connection": "keep-alive",
            "Authorization": f"Bearer {active_token}",
            "X-Website-Token": sha256(raw.encode()).hexdigest(),
            "X-BL": "en-US",
        }

    def __get_token(session):
        global gofile_token_cache
        headers = {
            "User-Agent": user_agent,
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "*/*",
            "Connection": "keep-alive",
        }

        if gofile_token_cache:
            try:
                test_headers = {**headers, "Authorization": f"Bearer {gofile_token_cache}"}
                test_res = session.get(
                    "https://api.gofile.io/accounts/website", headers=test_headers
                ).json()
                if test_res.get("status") == "ok":
                    return gofile_token_cache
            except Exception:
                pass

        __url = "https://api.gofile.io/accounts"
        try:
            __res = session.post(__url, headers=headers).json()
            if __res["status"] != "ok":
                raise DirectDownloadLinkException("ERROR: Failed to get token.")
            gofile_token_cache = __res["data"]["token"]
            return gofile_token_cache
        except Exception as e:
            raise e

    def __fetch_links(session, _id, folderPath=""):
        nonlocal token
        _url = f"https://api.gofile.io/contents/{_id}?cache=true"
        headers = __build_headers(token)
        if _password:
            _url += f"&password={_password}"
        try:
            _json = session.get(_url, headers=headers).json()
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")

        if _json.get("status") in {
            "error-unauth",
            "error-forbidden",
            "error-tokenInvalid",
        }:
            global gofile_token_cache
            gofile_token_cache = None
            try:
                token = __get_token(session)
                details["header"] = f"Cookie: accountToken={token}"
                _json = session.get(_url, headers=__build_headers(token)).json()
            except DirectDownloadLinkException:
                raise
            except Exception:
                raise DirectDownloadLinkException(
                    "ERROR: GoFile token revoked and failed to create new token."
                )

            if _json.get("status") in {
                "error-unauth",
                "error-forbidden",
                "error-tokenInvalid",
            }:
                raise DirectDownloadLinkException("ERROR: GoFile token revoked.")

        if _json.get("status") == "error-passwordRequired":
            raise DirectDownloadLinkException(
                f"ERROR:\n{PASSWORD_ERROR_MESSAGE.format(url)}"
            )
        if _json.get("status") == "error-passwordWrong":
            raise DirectDownloadLinkException("ERROR: This password is wrong !")
        if _json.get("status") == "error-notFound":
            raise DirectDownloadLinkException(
                "ERROR: File not found on gofile's server"
            )
        if _json.get("status") == "error-notPublic":
            raise DirectDownloadLinkException("ERROR: This folder is not public")

        data = _json["data"]

        if not details["title"]:
            details["title"] = data["name"] if data["type"] == "folder" else _id

        contents = data["children"]
        for content in contents.values():
            if content["type"] == "folder":
                if not content["public"]:
                    continue
                if not folderPath:
                    newFolderPath = ospath.join(details["title"], content["name"])
                else:
                    newFolderPath = ospath.join(folderPath, content["name"])
                __fetch_links(session, content["id"], newFolderPath)
            else:
                if not folderPath:
                    folderPath = details["title"]
                item = {
                    "path": ospath.join(folderPath),
                    "filename": content["name"],
                    "url": content["link"],
                }
                if "size" in content:
                    size = content["size"]
                    if isinstance(size, str) and size.isdigit():
                        size = float(size)
                    details["total_size"] += size
                details["contents"].append(item)

    details = {"contents": [], "title": "", "total_size": 0}
    with Session() as session:
        try:
            token = __get_token(session)
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
        details["header"] = f"Cookie: accountToken={token}"
        try:
            __fetch_links(session, _id)
        except Exception as e:
            raise DirectDownloadLinkException(e)

    if len(details["contents"]) == 1:
        return (details["contents"][0]["url"], details["header"])
    return details


def mediafireFolder(url):
    if "::" in url:
        _password = url.split("::")[-1]
        url = url.split("::")[-2]
    else:
        _password = ""
    try:
        raw = url.split("/", 4)[-1]
        folderkey = raw.split("/", 1)[0]
        folderkey = folderkey.split(",")
    except Exception:
        raise DirectDownloadLinkException("ERROR: Could not parse ")
    if len(folderkey) == 1:
        folderkey = folderkey[0]
    details = {"contents": [], "title": "", "total_size": 0, "header": ""}

    session = create_scraper()
    adapter = HTTPAdapter(
        max_retries=Retry(total=10, read=10, connect=10, backoff_factor=0.3)
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session = create_scraper(
        browser={"browser": "firefox", "platform": "windows", "mobile": False},
        delay=10,
        sess=session,
    )
    folder_infos = []

    def __get_info(folderkey):
        try:
            if isinstance(folderkey, list):
                folderkey = ",".join(folderkey)
            _json = session.post(
                "https://www.mediafire.com/api/1.5/folder/get_info.php",
                data={
                    "recursive": "yes",
                    "folder_key": folderkey,
                    "response_format": "json",
                },
            ).json()
        except Exception as e:
            raise DirectDownloadLinkException(
                f"ERROR: {e.__class__.__name__} While getting info"
            )
        _res = _json["response"]
        if "folder_infos" in _res:
            folder_infos.extend(_res["folder_infos"])
        elif "folder_info" in _res:
            folder_infos.append(_res["folder_info"])
        elif "message" in _res:
            raise DirectDownloadLinkException(f"ERROR: {_res['message']}")
        else:
            raise DirectDownloadLinkException("ERROR: something went wrong!")

    try:
        __get_info(folderkey)
    except Exception as e:
        raise DirectDownloadLinkException(e)

    details["title"] = folder_infos[0]["name"]

    def __scraper(url):
        with create_scraper() as session:
            parsed_url = urlparse(url)
            url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"

            def __repair_download(url):
                try:
                    html = HTML(session.get(url).text)
                    if new_link := html.xpath('//a[@id="continue-btn"]/@href'):
                        return __scraper(f"https://mediafire.com/{new_link[0]}")
                except Exception:
                    return

            try:
                html = HTML(session.get(url).text)
            except Exception:
                return
            if html.xpath("//div[@class='passwordPrompt']"):
                if not _password:
                    raise DirectDownloadLinkException(
                        f"ERROR: {PASSWORD_ERROR_MESSAGE}".format(url)
                    )
                try:
                    html = HTML(session.post(url, data={"downloadp": _password}).text)
                except Exception:
                    return
                if html.xpath("//div[@class='passwordPrompt']"):
                    return
            if final_link := html.xpath('//a[@aria-label="Download file"]/@href'):
                if final_link[0].startswith("//"):
                    return __scraper(f"https://{final_link[0][2:]}")
                return final_link[0]
            if repair_link := html.xpath("//a[@class='retry']/@href"):
                return __repair_download(repair_link[0])

    def __get_content(folderKey, folderPath="", content_type="folders"):
        try:
            params = {
                "content_type": content_type,
                "folder_key": folderKey,
                "response_format": "json",
            }
            _json = session.get(
                "https://www.mediafire.com/api/1.5/folder/get_content.php",
                params=params,
            ).json()
        except Exception as e:
            raise DirectDownloadLinkException(
                f"ERROR: {e.__class__.__name__} While getting content"
            )
        _res = _json["response"]
        if "message" in _res:
            raise DirectDownloadLinkException(f"ERROR: {_res['message']}")
        _folder_content = _res["folder_content"]
        if content_type == "folders":
            folders = _folder_content["folders"]
            for folder in folders:
                if folderPath:
                    newFolderPath = ospath.join(folderPath, folder["name"])
                else:
                    newFolderPath = ospath.join(folder["name"])
                __get_content(folder["folderkey"], newFolderPath)
            __get_content(folderKey, folderPath, "files")
        else:
            files = _folder_content["files"]
            for file in files:
                item = {}
                if not (_url := __scraper(file["links"]["normal_download"])):
                    continue
                item["filename"] = file["filename"]
                if not folderPath:
                    folderPath = details["title"]
                item["path"] = ospath.join(folderPath)
                item["url"] = _url
                if "size" in file:
                    size = file["size"]
                    if isinstance(size, str) and size.isdigit():
                        size = float(size)
                    details["total_size"] += size
                details["contents"].append(item)

    try:
        for folder in folder_infos:
            __get_content(folder["folderkey"], folder["name"])
    except Exception as e:
        raise DirectDownloadLinkException(e)
    finally:
        session.close()
    if len(details["contents"]) == 1:
        return (details["contents"][0]["url"], details["header"])
    return details


def cf_bypass(url):
    "DO NOT ABUSE THIS"
    try:
        data = {"cmd": "request.get", "url": url, "maxTimeout": 60000}
        _json = post(
            "https://cf.jmdkh.eu.org/v1",
            headers={"Content-Type": "application/json"},
            json=data,
        ).json()
        if _json["status"] == "ok":
            return _json["solution"]["response"]
    except Exception as e:
        e
    raise DirectDownloadLinkException("ERROR: Con't bypass cloudflare")


def send_cm_file(url, file_id=None):
    if "::" in url:
        _password = url.split("::")[-1]
        url = url.split("::")[-2]
    else:
        _password = ""
    _passwordNeed = False
    with create_scraper() as session:
        if file_id is None:
            try:
                html = HTML(session.get(url).text)
            except Exception as e:
                raise DirectDownloadLinkException(
                    f"ERROR: {e.__class__.__name__}"
                ) from e
            if html.xpath("//input[@name='password']"):
                _passwordNeed = True
            if not (file_id := html.xpath("//input[@name='id']/@value")):
                raise DirectDownloadLinkException("ERROR: file_id not found")
        try:
            data = {"op": "download2", "id": file_id}
            if _password and _passwordNeed:
                data["password"] = _password
            _res = session.post("https://send.cm/", data=data, allow_redirects=False)
            if "Location" in _res.headers:
                return (_res.headers["Location"], "Referer: https://send.cm/")
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
        if _passwordNeed:
            raise DirectDownloadLinkException(
                f"ERROR:\n{PASSWORD_ERROR_MESSAGE.format(url)}"
            )
        raise DirectDownloadLinkException("ERROR: Direct link not found")


def send_cm(url):
    if "/d/" in url:
        return send_cm_file(url)
    elif "/s/" not in url:
        file_id = url.split("/")[-1]
        return send_cm_file(url, file_id)
    splitted_url = url.split("/")
    details = {
        "contents": [],
        "title": "",
        "total_size": 0,
        "header": "Referer: https://send.cm/",
    }
    if len(splitted_url) == 5:
        url += "/"
        splitted_url = url.split("/")
    if len(splitted_url) >= 7:
        details["title"] = splitted_url[5]
    else:
        details["title"] = splitted_url[-1]
    session = Session()

    def __collectFolders(html):
        folders = []
        folders_urls = html.xpath("//h6/a/@href")
        folders_names = html.xpath("//h6/a/text()")
        for folders_url, folders_name in zip(folders_urls, folders_names):
            folders.append(
                {
                    "folder_link": folders_url.strip(),
                    "folder_name": folders_name.strip(),
                }
            )
        return folders

    def __getFile_link(file_id):
        try:
            _res = session.post(
                "https://send.cm/",
                data={"op": "download2", "id": file_id},
                allow_redirects=False,
            )
            if "Location" in _res.headers:
                return _res.headers["Location"]
        except Exception:
            pass

    def __getFiles(html):
        files = []
        hrefs = html.xpath('//tr[@class="selectable"]//a/@href')
        file_names = html.xpath('//tr[@class="selectable"]//a/text()')
        sizes = html.xpath('//tr[@class="selectable"]//span/text()')
        for href, file_name, size_text in zip(hrefs, file_names, sizes):
            files.append(
                {
                    "file_id": href.split("/")[-1],
                    "file_name": file_name.strip(),
                    "size": speed_string_to_bytes(size_text.strip()),
                }
            )
        return files

    def __writeContents(html_text, folderPath=""):
        folders = __collectFolders(html_text)
        for folder in folders:
            _html = HTML(cf_bypass(folder["folder_link"]))
            __writeContents(_html, ospath.join(folderPath, folder["folder_name"]))
        files = __getFiles(html_text)
        for file in files:
            if not (link := __getFile_link(file["file_id"])):
                continue
            item = {"url": link, "filename": file["filename"], "path": folderPath}
            details["total_size"] += file["size"]
            details["contents"].append(item)

    try:
        mainHtml = HTML(cf_bypass(url))
    except DirectDownloadLinkException as e:
        session.close()
        raise e
    except Exception as e:
        session.close()
        raise DirectDownloadLinkException(
            f"ERROR: {e.__class__.__name__} While getting mainHtml"
        )
    try:
        __writeContents(mainHtml, details["title"])
    except DirectDownloadLinkException as e:
        session.close()
        raise e
    except Exception as e:
        session.close()
        raise DirectDownloadLinkException(
            f"ERROR: {e.__class__.__name__} While writing Contents"
        )
    session.close()
    if len(details["contents"]) == 1:
        return (details["contents"][0]["url"], details["header"])
    return details


def doods(url):
    if "/e/" in url:
        url = url.replace("/e/", "/d/")
    parsed_url = urlparse(url)
    with create_scraper() as session:
        try:
            html = HTML(session.get(url).text)
        except Exception as e:
            raise DirectDownloadLinkException(
                f"ERROR: {e.__class__.__name__} While fetching token link"
            ) from e
        if not (link := html.xpath("//div[@class='download-content']//a/@href")):
            raise DirectDownloadLinkException(
                "ERROR: Token Link not found or maybe not allow to download! open in browser."
            )
        link = f"{parsed_url.scheme}://{parsed_url.hostname}{link[0]}"
        sleep(2)
        try:
            _res = session.get(link)
        except Exception as e:
            raise DirectDownloadLinkException(
                f"ERROR: {e.__class__.__name__} While fetching download link"
            ) from e
    if not (link := search(r"window\.open\('(\S+)'", _res.text)):
        raise DirectDownloadLinkException("ERROR: Download link not found try again")
    return (link.group(1), f"Referer: {parsed_url.scheme}://{parsed_url.hostname}/")


def easyupload(url):
    if "::" in url:
        _password = url.split("::")[-1]
        url = url.split("::")[-2]
    else:
        _password = ""
    file_id = url.split("/")[-1]
    with create_scraper() as session:
        try:
            _res = session.get(url)
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
        first_page_html = HTML(_res.text)
        if (
            first_page_html.xpath("//h6[contains(text(),'Password Protected')]")
            and not _password
        ):
            raise DirectDownloadLinkException(
                f"ERROR:\n{PASSWORD_ERROR_MESSAGE.format(url)}"
            )
        if not (
            match := search(
                r"https://eu(?:[1-9][0-9]?|100)\.easyupload\.io/action\.php", _res.text
            )
        ):
            raise DirectDownloadLinkException(
                "ERROR: Failed to get server for EasyUpload Link"
            )
        action_url = match.group()
        session.headers.update({"referer": "https://easyupload.io/"})
        recaptcha_params = {
            "k": "6LfWajMdAAAAAGLXz_nxz2tHnuqa-abQqC97DIZ3",
            "ar": "1",
            "co": "aHR0cHM6Ly9lYXN5dXBsb2FkLmlvOjQ0Mw..",
            "hl": "en",
            "v": "0hCdE87LyjzAkFO5Ff-v7Hj1",
            "size": "invisible",
            "cb": "c3o1vbaxbmwe",
        }
        if not (captcha_token := get_captcha_token(session, recaptcha_params)):
            raise DirectDownloadLinkException("ERROR: Captcha token not found")
        try:
            data = {
                "type": "download-token",
                "url": file_id,
                "value": _password,
                "captchatoken": captcha_token,
                "method": "regular",
            }
            json_resp = session.post(url=action_url, data=data).json()
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
    if "download_link" in json_resp:
        return json_resp["download_link"]
    elif "data" in json_resp:
        raise DirectDownloadLinkException(
            f"ERROR: Failed to generate direct link due to {json_resp['data']}"
        )
    raise DirectDownloadLinkException(
        "ERROR: Failed to generate direct link from EasyUpload."
    )


def filelions_and_streamwish(url):
    parsed_url = urlparse(url)
    hostname = parsed_url.hostname
    scheme = parsed_url.scheme
    if not hostname:
        raise DirectDownloadLinkException(
            "ERROR: URL is missing a hostname; cannot pick filelions/streamwish API."
        )
    apiKey = ""
    apiUrl = ""
    if any(
        x in hostname
        for x in [
            "filelions.co",
            "filelions.live",
            "filelions.to",
            "filelions.site",
            "cabecabean.lol",
            "filelions.online",
            "mycloudz.cc",
        ]
    ):
        apiKey = Config.FILELION_API
        apiUrl = "https://vidhideapi.com"
    elif any(
        x in hostname
        for x in [
            "embedwish.com",
            "kissmovies.net",
            "kitabmarkaz.xyz",
            "wishfast.top",
            "streamwish.to",
        ]
    ):
        apiKey = Config.STREAMWISH_API
        apiUrl = "https://api.streamwish.com"
    if not apiKey:
        raise DirectDownloadLinkException(
            f"ERROR: API is not provided get it from {scheme}://{hostname}"
        )
    file_code = url.split("/")[-1]
    quality = ""
    if bool(file_code.strip().endswith(("_o", "_h", "_n", "_l"))):
        spited_file_code = file_code.rsplit("_", 1)
        quality = spited_file_code[1]
        file_code = spited_file_code[0]
    url = f"{scheme}://{hostname}/{file_code}"
    with Session() as session:
        try:
            _res = session.get(
                f"{apiUrl}/api/file/direct_link",
                params={"key": apiKey, "file_code": file_code, "hls": "1"},
            ).json()
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
    if _res["status"] != 200:
        raise DirectDownloadLinkException(f"ERROR: {_res['msg']}")
    result = _res["result"]
    if not result["versions"]:
        raise DirectDownloadLinkException("ERROR: File Not Found")
    error = "\nProvide a quality to download the video\nAvailable Quality:"
    for version in result["versions"]:
        if quality == version["name"]:
            return version["url"]
        elif version["name"] == "l":
            error += "\nLow"
        elif version["name"] == "n":
            error += "\nNormal"
        elif version["name"] == "o":
            error += "\nOriginal"
        elif version["name"] == "h":
            error += "\nHD"
        error += f" <code>{url}_{version['name']}</code>"
    raise DirectDownloadLinkException(f"ERROR: {error}")


def streamvid(url: str):
    file_code = url.split("/")[-1]
    parsed_url = urlparse(url)
    url = f"{parsed_url.scheme}://{parsed_url.hostname}/d/{file_code}"
    quality_defined = bool(url.strip().endswith(("_o", "_h", "_n", "_l")))
    with create_scraper() as session:
        try:
            html = HTML(session.get(url).text)
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
        if quality_defined:
            data = {}
            if not (inputs := html.xpath('//form[@id="F1"]//input')):
                raise DirectDownloadLinkException("ERROR: No inputs found")
            for i in inputs:
                if key := i.get("name"):
                    data[key] = i.get("value")
            try:
                html = HTML(session.post(url, data=data).text)
            except Exception as e:
                raise DirectDownloadLinkException(
                    f"ERROR: {e.__class__.__name__}"
                ) from e
            if not (
                script := html.xpath(
                    '//script[contains(text(),"document.location.href")]/text()'
                )
            ):
                if error := html.xpath(
                    '//div[@class="alert alert-danger"][1]/text()[2]'
                ):
                    raise DirectDownloadLinkException(f"ERROR: {error[0]}")
                raise DirectDownloadLinkException(
                    "ERROR: direct link script not found!"
                )
            if directLink := findall(r'document\.location\.href="(.*)"', script[0]):
                return directLink[0]
            raise DirectDownloadLinkException(
                "ERROR: direct link not found! in the script"
            )
        elif (qualities_urls := html.xpath('//div[@id="dl_versions"]/a/@href')) and (
            qualities := html.xpath('//div[@id="dl_versions"]/a/text()[2]')
        ):
            error = "\nProvide a quality to download the video\nAvailable Quality:"
            for quality_url, quality in zip(qualities_urls, qualities):
                error += f"\n{quality.strip()} <code>{quality_url}</code>"
            raise DirectDownloadLinkException(f"ERROR: {error}")
        elif error := html.xpath('//div[@class="not-found-text"]/text()'):
            raise DirectDownloadLinkException(f"ERROR: {error[0]}")
        raise DirectDownloadLinkException("ERROR: Something went wrong")


def streamhub(url):
    file_code = url.split("/")[-1]
    parsed_url = urlparse(url)
    url = f"{parsed_url.scheme}://{parsed_url.hostname}/d/{file_code}"
    with create_scraper() as session:
        try:
            html = HTML(session.get(url).text)
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
        if not (inputs := html.xpath('//form[@name="F1"]//input')):
            raise DirectDownloadLinkException("ERROR: No inputs found")
        data = {}
        for i in inputs:
            if key := i.get("name"):
                data[key] = i.get("value")
        session.headers.update({"referer": url})
        sleep(1)
        try:
            html = HTML(session.post(url, data=data).text)
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
        if directLink := html.xpath(
            '//a[@class="btn btn-primary btn-go downloadbtn"]/@href'
        ):
            return directLink[0]
        if error := html.xpath('//div[@class="alert alert-danger"]/text()[2]'):
            raise DirectDownloadLinkException(f"ERROR: {error[0]}")
        raise DirectDownloadLinkException("ERROR: direct link not found!")


def pcloud(url):
    with create_scraper() as session:
        try:
            res = session.get(url)
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
    if link := findall(r".downloadlink.:..(https:.*)..", res.text):
        return link[0].replace(r"\/", "/")
    raise DirectDownloadLinkException("ERROR: Direct link not found")


def tmpsend(url):
    parsed_url = urlparse(url)
    if any(x in parsed_url.path for x in ["thank-you", "download"]):
        query_params = parse_qs(parsed_url.query)
        if file_id := query_params.get("d"):
            file_id = file_id[0]
    elif not (file_id := parsed_url.path.strip("/")):
        raise DirectDownloadLinkException("ERROR: Invalid URL format")
    referer_url = f"https://tmpsend.com/thank-you?d={file_id}"
    header = f"Referer: {referer_url}"
    download_link = f"https://tmpsend.com/download?d={file_id}"
    return download_link, header


def qiwi(url):
    # Based on https://github.com/aenulrofik
    with Session() as session:
        file_id = url.split("/")[-1]
        try:
            res = session.get(url).text
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
        tree = HTML(res)
        if name := tree.xpath('//h1[@class="page_TextHeading__VsM7r"]/text()'):
            ext = name[0].split(".")[-1]
            return f"https://spyderrock.com/{file_id}.{ext}"
        else:
            raise DirectDownloadLinkException("ERROR: File not found")


def mp4upload(url):
    with Session() as session:
        try:
            url = url.replace("embed-", "")
            req = session.get(url).text
            tree = HTML(req)
            inputs = tree.xpath("//input")
            header = {"Referer": "https://www.mp4upload.com/"}
            data = {input.get("name"): input.get("value") for input in inputs}
            if not data:
                raise DirectDownloadLinkException("ERROR: File Not Found!")
            post = session.post(
                url,
                data=data,
                headers={
                    "User-Agent": user_agent,
                    "Referer": "https://www.mp4upload.com/",
                },
            ).text
            tree = HTML(post)
            inputs = tree.xpath('//form[@name="F1"]//input')
            data = {
                input.get("name"): input.get("value").replace(" ", "")
                for input in inputs
            }
            if not data:
                raise DirectDownloadLinkException("ERROR: File Not Found!")
            data["referer"] = url
            direct_link = session.post(url, data=data).url
            return direct_link, header
        except Exception:
            raise DirectDownloadLinkException("ERROR: File Not Found!")


def berkasdrive(url):
    # By https://github.com/aenulrofik
    with Session() as session:
        try:
            sesi = session.get(url).text
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}") from e
    html = HTML(sesi)
    if link := html.xpath("//script")[0].text.split('"')[1]:
        return b64decode(link).decode("utf-8")
    else:
        raise DirectDownloadLinkException("ERROR: File Not Found!")


def swisstransfer(link):
    matched_link = match(
        r"https://www\.swisstransfer\.com/d/([\w-]+)(?:\:\:(\w+))?", link
    )
    if not matched_link:
        raise DirectDownloadLinkException(
            f"ERROR: Invalid SwissTransfer link format {link}"
        )

    transfer_id, password = matched_link.groups()
    password = password or ""

    def encode_password(password):
        return b64encode(password.encode("utf-8")).decode("utf-8") if password else ""

    def getfile(transfer_id, password):
        url = f"https://www.swisstransfer.com/api/links/{transfer_id}"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Authorization": encode_password(password) if password else "",
            "Content-Type": "application/json" if not password else "",
        }
        response = get(url, headers=headers)

        if response.status_code == 200:
            try:
                return response.json(), headers
            except ValueError:
                raise DirectDownloadLinkException(
                    f"ERROR: Error parsing JSON response {response.text}"
                )
        raise DirectDownloadLinkException(
            f"ERROR: Error fetching file details {response.status_code}, {response.text}"
        )

    def gettoken(password, containerUUID, fileUUID):
        url = "https://www.swisstransfer.com/api/generateDownloadToken"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/json",
        }
        body = {
            "password": password,
            "containerUUID": containerUUID,
            "fileUUID": fileUUID,
        }

        response = post(url, headers=headers, json=body)

        if response.status_code == 200:
            return response.text.strip().replace('"', "")
        raise DirectDownloadLinkException(
            f"ERROR: Error generating download token {response.status_code}, {response.text}"
        )

    data, headers = getfile(transfer_id, password)
    if not data:
        return None

    try:
        container_uuid = data["data"]["containerUUID"]
        download_host = data["data"]["downloadHost"]
        files = data["data"]["container"]["files"]
        folder_name = data["data"]["container"]["message"] or "unknown"
    except (KeyError, IndexError, TypeError) as e:
        raise DirectDownloadLinkException(f"ERROR: Error parsing file details {e}")

    total_size = sum(file["fileSizeInBytes"] for file in files)

    if len(files) == 1:
        file = files[0]
        file_uuid = file["UUID"]
        token = gettoken(password, container_uuid, file_uuid)
        download_url = f"https://{download_host}/api/download/{transfer_id}/{file_uuid}?token={token}"
        return download_url, "User-Agent:Mozilla/5.0"

    contents = []
    for file in files:
        file_uuid = file["UUID"]
        file_name = file["fileName"]
        file_size = file["fileSizeInBytes"]

        token = gettoken(password, container_uuid, file_uuid)
        if not token:
            continue

        download_url = f"https://{download_host}/api/download/{transfer_id}/{file_uuid}?token={token}"
        contents.append({"filename": file_name, "path": "", "url": download_url})

    return {
        "contents": contents,
        "title": folder_name,
        "total_size": total_size,
        "header": "User-Agent:Mozilla/5.0",
    }


def instagram(link: str) -> str:
    api_url = Config.INSTADL_API or "https://instagramcdn.vercel.app"
    full_url = f"{api_url}/api/video?postUrl={link}"

    try:
        response = get(full_url)
        response.raise_for_status()
        data = response.json()

        if (
            data.get("status") == "success"
            and "data" in data
            and "videoUrl" in data["data"]
        ):
            return data["data"]["videoUrl"]

        raise DirectDownloadLinkException("ERROR: Failed to retrieve video URL.")

    except Exception as e:
        raise DirectDownloadLinkException(f"ERROR: {e}")


# ============================ GDFlix & HubCloud family ============================


def is_gdflix(url: str):
    netloc = urlparse(url).netloc.lower()
    return "gdflix" in netloc or any(h in netloc for h in GDFLIX_DOMAINS)


def is_hubcloud(url: str):
    netloc = urlparse(url).netloc.lower()
    return "hubcloud" in netloc or any(h in netloc for h in HUBCLOUD_DOMAINS)


def is_hubdrive(url: str):
    netloc = urlparse(url).netloc.lower()
    return "hubdrive" in netloc or any(h in netloc for h in HUBDRIVE_DOMAINS)


def is_hubcdn(url: str):
    netloc = urlparse(url).netloc.lower()
    return "hubcdn" in netloc or any(h in netloc for h in HUBCDN_DOMAINS)


def is_hblinks(url: str):
    return "hblinks" in urlparse(url).netloc.lower()


def _base_url(url: str):
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}"


def _hub_classify_server(text: str):
    t = text.lower()
    for label, keywords in HUB_SERVER_LABELS:
        if any(k in t for k in keywords):
            return label
    return None


def _hub_size_to_bytes(size_str):
    if not size_str or size_str == "Unknown":
        return 0
    size_str = str(size_str).lower().strip()
    m = match(r"([\d\.]+)\s*(kb|mb|gb|tb|b)?", size_str)
    if not m:
        return 0
    val = float(m.group(1))
    unit = m.group(2)
    if not unit:
        return int(val)
    factors = {
        "b": 1,
        "kb": 1024,
        "mb": 1048576,
        "gb": 1073741824,
        "tb": 1099511627776,
    }
    return int(val * factors.get(unit, 1))


def _hub_pick_server(servers):
    """Pick the fastest available mirror, falling back through HUB_SERVER_ORDER."""
    for label in HUB_SERVER_ORDER:
        if label in servers:
            return servers[label]
    return next(iter(servers.values()), None)


def _cf_session():
    """A curl_cffi session impersonating Chrome; required to pass GDFlix/HubCloud TLS checks."""
    try:
        from curl_cffi.requests import Session as CFSession
    except ImportError as e:
        raise DirectDownloadLinkException(
            "ERROR: curl_cffi is required for GDFlix/HubCloud links"
        ) from e
    return CFSession(impersonate="chrome120")


def _soup(text):
    try:
        from bs4 import BeautifulSoup
    except ImportError as e:
        raise DirectDownloadLinkException(
            "ERROR: beautifulsoup4 is required for GDFlix/HubCloud links"
        ) from e
    return BeautifulSoup(text, "html.parser")


def _hub_fetch(session, url, retries=3, wait=4, follow=True):
    for attempt in range(1, retries + 1):
        try:
            r = session.get(url, headers=HEADERS, timeout=30, allow_redirects=follow)
            if r.status_code in (200, 301, 302):
                return r
            if r.status_code == 404:
                raise DirectDownloadLinkException(f"ERROR: Not found (404): {url}")
            LOGGER.info(f"HTTP {r.status_code} for {url} — retrying in {wait}s")
        except DirectDownloadLinkException:
            raise
        except Exception as e:
            LOGGER.info(f"Fetch error for {url}: {e}")
        if attempt < retries:
            sleep(wait)
    raise DirectDownloadLinkException(f"ERROR: All {retries} attempts failed for {url}")


def _gdf_get_file_links(session, url):
    r = _hub_fetch(session, url)
    soup = _soup(r.text)
    links = {"instant": "", "r2": "", "telegram": "", "gofile": "", "multiup": ""}
    filename = "Unknown"
    size = "Unknown"
    if soup.title:
        filename = soup.title.text.replace("GDFlix |", "").strip()
    for li in soup.find_all("li"):
        txt = li.get_text(" ", strip=True)
        if txt.startswith("Size :"):
            size = txt.split("Size :", 1)[1].split("|")[0].strip()
    for a in soup.find_all("a", href=True):
        href = urljoin(url, a["href"])
        text = a.get_text(" ", strip=True).lower()
        if "instant dl" in text:
            links["instant"] = href
        elif "cloud download" in text:
            links["r2"] = href
        elif "telegram" in text:
            links["telegram"] = href
        elif "gofile" in text:
            links["gofile"] = href
        if "validate.multiup2.workers.dev" in href:
            links["multiup"] = href
    return filename, size, links


def _gdf_get_mirror_links(session, url):
    mirrors = {}
    if not url:
        return mirrors
    try:
        r = _hub_fetch(session, url)
        soup = _soup(r.text)
        for tag in soup.find_all("a", class_="host"):
            name = tag.get("namehost") or tag.get("nameHost", "").strip()
            link = tag.get("link") or tag.get("href", "").strip()
            validity = tag.get("validity", "").strip().lower()
            if not name or not link or link.startswith("/"):
                continue
            mirrors[name] = {"url": link, "valid": validity == "valid"}
        if not mirrors:
            html = r.text
            pats = {
                "Megaup": r'(?i)https?://(?:www\.)?megaup\.net/[^\s"\'&]+',
                "1fichier": r'(?i)https?://(?:www\.)?1fichier\.com/\?[^\s"\'&]+',
                "Pixeldrain": r'(?i)https?://pixeldrain\.com/[^\s"\'&]+',
                "Mediafire": r'(?i)https?://(?:www\.)?mediafire\.com/[^\s"\'&]+',
                "BuzzHeavier": r'(?i)https?://(?:www\.)?buzzheavier\.com/[^\s"\'&]+',
                "GoFile": r'(?i)https?://gofile\.io/[^\s"\'&]+',
            }
            for name, pat in pats.items():
                if m := search(pat, html):
                    mirrors[name] = {"url": m.group(0), "valid": True}
    except Exception as e:
        LOGGER.info(f"GDFlix mirror fetch failed: {e}")
    return mirrors


def _gdf_resolve_instant_dl(session, instant_url):
    if not instant_url:
        return ""
    try:
        r = _hub_fetch(session, instant_url, follow=False)
        if r.status_code in (301, 302):
            loc = r.headers.get("Location", "")
            if loc:
                gdrive = parse_qs(urlparse(loc).query).get("url", [""])[0]
                if "googleusercontent.com" in gdrive or "drive.google.com" in gdrive:
                    return gdrive
                if "googleusercontent.com" in loc or "drive.google.com" in loc:
                    return loc
        html = r.text
        for a in _soup(html).find_all("a", href=True):
            href = a["href"].strip()
            if "googleusercontent.com" in href or "drive.google.com" in href:
                return href
        if m := search(
            r'(?i)https?://[^\s"\'<>\\]*(?:googleusercontent\.com|drive\.google\.com)/[^\s"\'<>\\]+',
            html,
        ):
            return m.group(0)
    except Exception as e:
        LOGGER.info(f"GDFlix instant DL resolve failed: {e}")
    return ""


def _gdf_get_pack_info(session, url):
    r = _hub_fetch(session, url)
    soup = _soup(r.text)
    root = _base_url(url)
    title = "Unknown Pack"
    if h3 := soup.find("h3"):
        title = sub(r"\s*\[.*?\]\s*$", "", h3.get_text(" ", strip=True)).strip()
    total_size = "Unknown"
    size_el = soup.find(id="pack_size")
    if size_el and size_el.get("data-total"):
        total_size = size_el["data-total"]
    files = []
    for li in soup.find_all("li", class_="list-group-item"):
        a = li.find("a", href=True)
        if not a:
            continue
        href = a["href"].strip()
        if "/file/" not in href:
            continue
        raw = a.get_text(strip=True)
        size_m = search(r"\[([^\]]+)\]\s*$", raw)
        files.append(
            {
                "name": sub(r"\s*\[.*?\]\s*$", "", raw).strip(),
                "size": size_m.group(1) if size_m else "",
                "url": href if href.startswith("http") else root + href,
            }
        )
    return title, total_size, files


def _gdflix_file_resolver(session, url):
    _filename, _size, links = _gdf_get_file_links(session, url)

    if gdrive_link := _gdf_resolve_instant_dl(session, links.get("instant")):
        return gdrive_link

    gofile_url = links.get("gofile") or ""
    if not gofile_url and (mirror_url := links.get("multiup")):
        mirrors = _gdf_get_mirror_links(session, mirror_url)
        if "GoFile" in mirrors:
            gofile_url = mirrors["GoFile"].get("url") or ""

    if gofile_url:
        try:
            return gofile(gofile_url)
        except Exception as e:
            raise DirectDownloadLinkException(
                f"ERROR: Instant DL failed and GoFile fallback failed: {e}"
            ) from e

    raise DirectDownloadLinkException(
        "ERROR: Instant DL failed and no GoFile link found!"
    )


def _hub_get_pack_info(session, url):
    r = _hub_fetch(session, url)
    root = _base_url(url)
    title = "Unknown Pack"
    total_size = "Unknown"
    files = []
    if m := search(r"const packData\s*=\s*JSON\.parse\(`(.*?)`\);", r.text):
        try:
            data = loads(m.group(1))
            title = data.get("pack", {}).get("pack_name", title)
            pack_files = data.get("files", [])
            total_size = str(sum(int(f.get("file_size", 0)) for f in pack_files))
            for file in pack_files:
                files.append(
                    {
                        "name": file.get("file_name", "Unknown"),
                        "size": str(int(file.get("file_size", 0))),
                        "url": f"{root}/video/{file.get('share_id', '')}",
                    }
                )
        except Exception as e:
            LOGGER.info(f"HubCloud pack JSON decode error: {e}")
    return title, total_size, files


def _hub_parse_hblinks(session, url):
    r = _hub_fetch(session, url)
    soup = _soup(r.text)
    title = soup.title.text.strip() if soup.title else "Unknown"
    for s in ["– HUBLinks", "- HUBLinks", "| HUBLinks"]:
        title = title.replace(s, "").strip()
    groups = []
    for tag in soup.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6", "li"]):
        valid_links = [
            a["href"].strip()
            for a in tag.find_all("a", href=True)
            if is_hubcloud(a["href"].strip())
            or is_hubdrive(a["href"].strip())
            or is_hubcdn(a["href"].strip())
        ]
        if not valid_links:
            continue
        qual = tag.get_text(" ", strip=True)
        for sep_str in ["–", "-", "|"]:
            if sep_str in qual:
                qual = qual.split(sep_str)[0].strip()
        chosen = next((l for l in valid_links if is_hubcloud(l)), valid_links[0])
        groups.append({"quality": qual, "url": chosen, "all_urls": valid_links})
    return title, groups


def _hub_parse_drive(session, url, _depth=0):
    r = _hub_fetch(session, url)
    soup = _soup(r.text)
    # Some drive pages only link onward to the actual HubCloud server page.
    if _depth < 3:
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if "hubcloud server" in a.get_text(strip=True).lower() and href != url:
                return _hub_parse_drive(session, href, _depth + 1)

    info = {
        "filename": "Unknown",
        "size": "Unknown",
        "filetype": "Unknown",
        "date": "Unknown",
        "token_url": "",
        "is_direct": False,
    }
    if header := soup.find("div", class_="card-header"):
        info["filename"] = header.get_text(strip=True)
    for li in soup.find_all("li", class_="list-group-item"):
        i_tag = li.find("i")
        val = i_tag.get_text(strip=True) if i_tag else ""
        text = li.get_text(" ", strip=True)
        if "File Size" in text:
            info["size"] = val
        elif "File Type" in text:
            info["filetype"] = val
        elif "Share Date" in text:
            info["date"] = val

    dl = None
    for a_id in ["download", "downloadBtn"]:
        found = soup.find("a", id=a_id)
        if found and found.get("href") and found.get("href") != "#":
            dl = found
            break

    if dl:
        href = dl["href"].strip()
        info["token_url"] = href
        info["is_direct"] = not ("hubcloud.php" in href or "host=" in href)
        return info

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if "hubcloud.php" in href or "host=" in href:
            info["token_url"] = href
            return info

    video_dl = soup.find(string=lambda t: t and "Generate Direct Download Link" in t)
    if video_dl and video_dl.find_parent("a"):
        info["token_url"] = video_dl.find_parent("a")["href"].strip()
    elif m := search(r"var\s+url\s*=\s*['\"]([^'\"]+)['\"]", r.text):
        info["token_url"] = m.group(1)
    return info


def _hub_resolve_servers(session, token_url):
    if not token_url:
        return {}
    try:
        r = _hub_fetch(session, token_url, follow=True)
        soup = _soup(r.text)

        for a_id in ["download", "downloadBtn"]:
            found = soup.find("a", id=a_id)
            if found and found.get("href") and found.get("href") != "#":
                href = found["href"].strip()
                if not ("hubcloud.php" in href or "host=" in href):
                    return {"Direct": href}
                break

        servers = {}
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href.startswith("http"):
                continue
            if any(s in href for s in HUB_SKIP_DOMAINS):
                continue
            if label := _hub_classify_server(a.get_text(strip=True)):
                servers[label] = href
            elif any(ext in href for ext in [".mkv", ".mp4", ".zip", ".rar"]):
                servers.setdefault("Direct", href)
        return servers
    except Exception as e:
        LOGGER.info(f"Could not resolve HubCloud server links: {e}")
        return {}


def _hubcloud_file_resolver(session, url):
    info = _hub_parse_drive(session, url)
    filename = info.get("filename") or "File"
    size = _hub_size_to_bytes(info.get("size"))

    if not info.get("token_url"):
        return url, filename, size
    if info.get("is_direct"):
        return info["token_url"], filename, size

    servers = _hub_resolve_servers(session, info["token_url"])
    resolved_url = _hub_pick_server(servers) or url

    # Intermediate pages (e.g. pixel.hubcloud.cx) still need one more hop.
    if (
        "googleusercontent.com" not in resolved_url
        and "r2.cloudflarestorage.com" not in resolved_url
    ):
        try:
            fsoup = _soup(_hub_fetch(session, resolved_url, follow=True).text)
            for a_id in ["download", "downloadBtn"]:
                fdl = fsoup.find("a", id=a_id)
                if fdl and fdl.get("href") and fdl.get("href") != "#":
                    resolved_url = fdl["href"].strip()
                    break
            if "googleusercontent.com" not in resolved_url:
                for a in fsoup.find_all("a", href=True):
                    if "googleusercontent.com" in a["href"]:
                        resolved_url = a["href"].strip()
                        break
        except Exception as e:
            LOGGER.info(f"HubCloud final hop failed, using {resolved_url}: {e}")

    return resolved_url, filename, size


def gdflix(url: str):
    with _cf_session() as session:
        if "/pack/" not in url:
            return _gdflix_file_resolver(session, url)

        title, _total_size, files = _gdf_get_pack_info(session, url)
        if not files:
            raise DirectDownloadLinkException("ERROR: No files found in pack.")

        details = {"contents": [], "title": title, "total_size": 0}

        def process_gdf_file(file_info):
            try:
                with _cf_session() as thread_session:
                    return (
                        file_info,
                        _gdflix_file_resolver(thread_session, file_info["url"]),
                        None,
                    )
            except Exception as e:
                return file_info, None, e

        results = [None] * len(files)
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(process_gdf_file, f): i for i, f in enumerate(files)}
            for future in as_completed(futures):
                results[futures[future]] = future.result()

        for res in results:
            if not res:
                continue
            file_info, resolved_link, err = res
            if err:
                LOGGER.error(f"Failed to resolve file {file_info['name']}: {err}")
                continue
            if not resolved_link:
                continue

            header = None
            if isinstance(resolved_link, tuple):
                resolved_url = resolved_link[0]
                if len(resolved_link) == 2:
                    header = resolved_link[1]
            elif isinstance(resolved_link, dict):
                # A GoFile fallback returned a multi-file payload; splice it in.
                details["contents"].extend(resolved_link.get("contents", []))
                details["total_size"] += resolved_link.get("total_size", 0)
                if resolved_link.get("header") and "header" not in details:
                    details["header"] = resolved_link["header"]
                continue
            else:
                resolved_url = resolved_link

            details["contents"].append(
                {
                    "url": resolved_url,
                    "filename": file_info["name"],
                    "path": "",
                }
            )
            details["total_size"] += _hub_size_to_bytes(file_info.get("size"))
            if header and "header" not in details:
                details["header"] = header

        if not details["contents"]:
            raise DirectDownloadLinkException(
                "ERROR: All files in pack failed to resolve."
            )
        return details


def hubcloud(url: str):
    with _cf_session() as session:
        if "/pack/" in url or "/packs/" in url:
            title, _total_size, files = _hub_get_pack_info(session, url)
            if not files:
                raise DirectDownloadLinkException("ERROR: No files found in pack.")

            details = {"contents": [], "title": title, "total_size": 0}

            def process_hub_file(file_info):
                try:
                    with _cf_session() as thread_session:
                        resolved_url, fname, fsize = _hubcloud_file_resolver(
                            thread_session, file_info["url"]
                        )
                        return file_info, resolved_url, fname, fsize, None
                except Exception as e:
                    return file_info, None, None, 0, e

            results = [None] * len(files)
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {
                    executor.submit(process_hub_file, f): i for i, f in enumerate(files)
                }
                for future in as_completed(futures):
                    results[futures[future]] = future.result()

            for res in results:
                if not res:
                    continue
                file_info, resolved_url, fname, fsize, err = res
                if err:
                    LOGGER.error(f"Failed to resolve file {file_info['name']}: {err}")
                    continue
                if not resolved_url:
                    continue
                details["contents"].append(
                    {
                        "url": resolved_url,
                        "filename": fname or file_info["name"],
                        "path": "",
                    }
                )
                details["total_size"] += fsize

            if not details["contents"]:
                raise DirectDownloadLinkException(
                    "ERROR: All files in pack failed to resolve."
                )
            return details

        if is_hblinks(url):
            title, groups = _hub_parse_hblinks(session, url)
            if not groups:
                raise DirectDownloadLinkException(
                    "ERROR: No valid links found in post."
                )

            details = {"contents": [], "title": title, "total_size": 0}
            for grp in groups:
                try:
                    info = _hub_parse_drive(session, grp["url"])
                    servers = (
                        _hub_resolve_servers(session, info["token_url"])
                        if info.get("token_url")
                        else {}
                    )

                    # HubDrive / HubCDN siblings in the same post act as extra mirrors.
                    if (hd := [l for l in grp["all_urls"] if is_hubdrive(l)]) and (
                        "FSL" not in servers
                    ):
                        servers["FSL"] = hd[0]
                    if (hcdn := [l for l in grp["all_urls"] if is_hubcdn(l)]) and (
                        "10Gbps" not in servers
                    ):
                        servers["10Gbps"] = hcdn[0]

                    if not (resolved_url := _hub_pick_server(servers)):
                        continue

                    name = info.get("filename")
                    if not name or name == "Unknown":
                        name = grp["quality"]

                    details["contents"].append(
                        {"url": resolved_url, "filename": name, "path": ""}
                    )
                    details["total_size"] += _hub_size_to_bytes(info.get("size"))
                except Exception as e:
                    LOGGER.error(f"Failed resolving group in HBLinks post: {e}")
                    continue

            if not details["contents"]:
                raise DirectDownloadLinkException(
                    "ERROR: All files in HBLinks post failed to resolve."
                )
            return details

        resolved_url, fname, fsize = _hubcloud_file_resolver(session, url)
        return {
            "contents": [{"url": resolved_url, "filename": fname, "path": ""}],
            "title": fname,
            "total_size": fsize,
        }
