from bot.helper.mirror_leech_utils.download_utils.direct_link_generator import (
    __parse_content_disposition,
    _filename_from_cd,
)


def test_parse_content_disposition_unquoted_with_spaces():
    cd = "attachment; filename=Gossip Girl S01-S06 Season 1-6 Complete 720p HDTV x264-[maximersk].zip"
    assert (
        __parse_content_disposition(cd)
        == "Gossip Girl S01-S06 Season 1-6 Complete 720p HDTV x264-[maximersk].zip"
    )
    assert (
        _filename_from_cd(cd)
        == "Gossip Girl S01-S06 Season 1-6 Complete 720p HDTV x264-[maximersk].zip"
    )


def test_parse_content_disposition_quoted():
    cd = 'attachment; filename="Gossip Girl S01-S06 Season 1-6.zip"'
    assert __parse_content_disposition(cd) == "Gossip Girl S01-S06 Season 1-6.zip"


def test_parse_content_disposition_utf8_rfc5987():
    cd = "attachment; filename*=UTF-8''Dark%20S01%20720p.zip"
    assert __parse_content_disposition(cd) == "Dark S01 720p.zip"


def test_parse_content_disposition_utf8_with_lang():
    cd = "attachment; filename*=utf-8'en'Dark%20S01%20720p.zip"
    assert __parse_content_disposition(cd) == "Dark S01 720p.zip"


def test_parse_content_disposition_case_insensitive():
    cd = 'inline; FILENAME=sample_video.mkv; modification-date="Wed, 12 Feb 2020 12:34:56 GMT"'
    assert __parse_content_disposition(cd) == "sample_video.mkv"


def test_parse_content_disposition_empty_or_none():
    assert __parse_content_disposition(None) is None
    assert __parse_content_disposition("") is None
    assert __parse_content_disposition("attachment") is None
