from unittest.mock import patch
from bot.helper.mirror_leech_utils.download_utils.direct_link_generator import (
    __parse_content_disposition,
    _filename_from_cd,
    direct_link_generator,
    is_supported_direct_link,
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


def test_torbox_tb_cdn_st_domain_resolution():
    test_url = "https://store-022.weur.tb-cdn.st/zip/a513fbcf-39c8-4304-81f4-4fdf8b47968a?token=e9ac95f6-c5ce-497f-8f23-7e03b4a8d1f5"
    mock_response = {
        "contents": [
            {
                "path": "",
                "filename": "Gossip Girl S01-S06 Season 1-6 Complete 720p HDTV x264-[maximersk].zip",
                "url": test_url,
            }
        ],
        "title": "Gossip Girl S01-S06 Season 1-6 Complete 720p HDTV x264-[maximersk].zip",
        "total_size": 109513011652,
    }
    with patch(
        "bot.helper.mirror_leech_utils.download_utils.direct_link_generator.direct_stream_link",
        return_value=mock_response,
    ) as mock_dsl:
        res = direct_link_generator(test_url)
        mock_dsl.assert_called_once_with(test_url)
        assert (
            res["title"]
            == "Gossip Girl S01-S06 Season 1-6 Complete 720p HDTV x264-[maximersk].zip"
        )
        assert res["total_size"] == 109513011652


def test_is_supported_direct_link():
    assert (
        is_supported_direct_link(
            "https://store-022.weur.tb-cdn.st/zip/a513fbcf-39c8-4304-81f4"
        )
        is True
    )
    assert is_supported_direct_link("https://gofile.io/d/xyz") is True
    assert is_supported_direct_link("https://mediafire.com/file/xyz") is True
    assert is_supported_direct_link("https://randomsite.com/video.mp4") is False
