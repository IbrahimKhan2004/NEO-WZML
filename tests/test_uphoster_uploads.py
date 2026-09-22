import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from bot.helper.mirror_leech_utils.uphoster_utils.storageto_utils.upload import (
    StorageToUpload,
)
from bot.helper.mirror_leech_utils.uphoster_utils.gofile_utils.upload import (
    GoFileUpload,
)


class DummyListener:
    def __init__(self):
        self.user_id = 123456
        self.is_cancelled = False
        self.name = "test_file.mkv"

    async def on_upload_error(self, error):
        pass

    async def on_upload_complete(self, *args, **kwargs):
        pass


class TestStorageToUpload(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.listener = DummyListener()
        with patch("bot.user_data", {}):
            self.uploader = StorageToUpload(self.listener, "/tmp/fake_file.mkv")

    def test_headers_anonymous_with_owner_token(self):
        self.uploader.token = None
        headers = self.uploader._StorageToUpload__headers(owner_token="owner_123")
        self.assertEqual(headers.get("Authorization"), "Owner owner_123")
        self.assertNotIn("X-Owner-Token", headers)

    def test_headers_authenticated_with_owner_token(self):
        self.uploader.token = "bearer_abc"
        headers = self.uploader._StorageToUpload__headers(owner_token="owner_123")
        self.assertEqual(headers.get("Authorization"), "Bearer bearer_abc")
        self.assertEqual(headers.get("X-Owner-Token"), "owner_123")


class TestGoFileUpload(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.listener = DummyListener()
        with patch("bot.user_data", {}):
            self.uploader = GoFileUpload(self.listener, "/tmp/fake_file.mkv")

    @patch("bot.helper.mirror_leech_utils.uphoster_utils.gofile_utils.upload.GoFileUpload._GoFileUpload__getServer")
    @patch("bot.helper.mirror_leech_utils.uphoster_utils.gofile_utils.upload.GoFileUpload.upload_aiohttp")
    async def test_upload_file_server_fallback(self, mock_upload_aiohttp, mock_get_server):
        mock_get_server.return_value = [{"name": "store1"}, {"name": "store2"}]

        # First call fails, second call succeeds
        mock_upload_aiohttp.side_effect = [
            Exception("HTTP 500: Internal Server Error"),
            {"status": "ok", "data": {"downloadPage": "https://gofile.io/d/abc"}},
        ]

        with patch.object(self.uploader, "_GoFileUpload__resp_handler", side_effect=lambda x: x["data"]):
            res = await self.uploader.upload_file("/tmp/fake_file.mkv")
            self.assertEqual(res["downloadPage"], "https://gofile.io/d/abc")
            self.assertEqual(mock_upload_aiohttp.call_count, 2)


if __name__ == "__main__":
    unittest.main()
