# This file is a part of NEO-WZML (github.com/IbrahimKhan2004/NEO-WZML)

from io import BufferedReader
from mimetypes import guess_type
from os import path as ospath
from os import walk as oswalk
from logging import getLogger
from pathlib import Path
from uuid import uuid4

from aiofiles.os import path as aiopath
from aiohttp import ClientSession
from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from bot.core.config_manager import Config
from bot.helper.ext_utils.bot_utils import SetInterval, sync_to_async

LOGGER = getLogger(__name__)


class ProgressFileReader(BufferedReader):
    def __init__(self, filename, read_callback=None):
        super().__init__(open(filename, "rb"))
        self.__read_callback = read_callback
        self.length = Path(filename).stat().st_size

    def read(self, size=None):
        size = size or (self.length - self.tell())
        if self.__read_callback:
            self.__read_callback(self.tell())
        return super().read(size)

    def __len__(self):
        return self.length


class StorageToUpload:
    def __init__(self, listener, path):
        self.listener = listener
        self._updater = None
        self._path = path
        self._is_errored = False
        self.api_url = "https://storage.to/api/"
        self.__processed_bytes = 0
        self.last_uploaded = 0
        self.total_time = 0
        self.total_files = 0
        self.total_folders = 0
        self.is_uploading = True
        self.update_interval = 3

        from bot import user_data

        user_dict = user_data.get(self.listener.user_id, {})
        self.token = user_dict.get("STORAGETO_TOKEN") or Config.STORAGETO_TOKEN
        self.visitor_token = uuid4().hex

    @property
    def speed(self):
        try:
            return self.__processed_bytes / self.total_time
        except Exception:
            return 0

    @property
    def processed_bytes(self):
        return self.__processed_bytes

    def __progress_callback(self, current):
        chunk_size = current - self.last_uploaded
        self.last_uploaded = current
        self.__processed_bytes += chunk_size

    async def progress(self):
        self.total_time += self.update_interval

    def __headers(self, owner_token=None):
        headers = {"X-Visitor-Token": self.visitor_token}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if owner_token:
            headers["X-Owner-Token"] = owner_token
        return headers

    @retry(
        wait=wait_exponential(multiplier=2, min=4, max=8),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(Exception),
    )
    async def __put_part(self, url, data):
        async with ClientSession() as session:
            async with session.put(url, data=data) as resp:
                if resp.status not in [200, 201]:
                    raise Exception(f"HTTP {resp.status}: {await resp.text()}")
                return resp.headers.get("ETag", "")

    async def upload_file(self, path: str, collection_id: str = ""):
        if self.listener.is_cancelled:
            return None

        file_name = ospath.basename(path).replace(" ", ".")[:255]
        size = (await aiopath.stat(path)).st_size
        content_type = guess_type(file_name)[0] or "application/octet-stream"

        async with ClientSession() as session:
            async with session.post(
                f"{self.api_url}upload/init",
                json={"filename": file_name, "content_type": content_type, "size": size},
                headers=self.__headers(),
            ) as resp:
                if resp.status not in [200, 201]:
                    raise Exception(f"Init Failed: {await resp.text()}")
                init_res = await resp.json()

        owner_token = init_res.get("owner_token")
        with ProgressFileReader(
            filename=path, read_callback=self.__progress_callback
        ) as file:
            if init_res.get("type") == "multipart":
                part_size = init_res["part_size"]
                urls = init_res["initial_urls"]
                parts = []
                part_no = 1
                while True:
                    chunk = file.read(part_size)
                    if not chunk:
                        break
                    url = urls.get(str(part_no))
                    if not url:
                        async with ClientSession() as session:
                            async with session.post(
                                f"{self.api_url}upload/parts",
                                json={
                                    "upload_id": init_res["upload_id"],
                                    "part_numbers": [part_no],
                                },
                                headers=self.__headers(owner_token),
                            ) as resp:
                                url = (await resp.json())["part_urls"][0]["url"]
                    etag = await self.__put_part(url, chunk)
                    parts.append({"partNumber": part_no, "etag": etag})
                    part_no += 1

                async with ClientSession() as session:
                    async with session.post(
                        f"{self.api_url}upload/complete-multipart",
                        json={"upload_id": init_res["upload_id"], "parts": parts},
                        headers=self.__headers(owner_token),
                    ) as resp:
                        if resp.status not in [200, 201]:
                            raise Exception(f"Complete Failed: {await resp.text()}")
            else:
                await self.__put_part(init_res["upload_url"], file)

        confirm_body = {
            "filename": file_name,
            "size": size,
            "content_type": content_type,
            "r2_key": init_res["r2_key"],
        }
        if collection_id:
            confirm_body["collection_id"] = collection_id

        async with ClientSession() as session:
            async with session.post(
                f"{self.api_url}upload/confirm",
                json=confirm_body,
                headers=self.__headers(owner_token),
            ) as resp:
                if resp.status not in [200, 201]:
                    raise Exception(f"Confirm Failed: {await resp.text()}")
                return await resp.json()

    async def _upload_dir(self, input_directory):
        file_list = [
            ospath.join(root, file)
            for root, _, files in await sync_to_async(oswalk, input_directory)
            for file in files
        ]
        if not file_list:
            raise Exception("No files found in folder.")

        async with ClientSession() as session:
            async with session.post(
                f"{self.api_url}collection",
                json={"expected_file_count": len(file_list)},
                headers=self.__headers(),
            ) as resp:
                if resp.status not in [200, 201]:
                    raise Exception(f"Collection Creation Failed: {await resp.text()}")
                collection_id = (await resp.json())["collection"]["id"]

        for file_path in file_list:
            if self.listener.is_cancelled:
                break
            if await self.upload_file(file_path, collection_id):
                self.total_files += 1

        return collection_id

    async def upload(self):
        try:
            LOGGER.info(f"StorageTo Uploading: {self._path}")
            self._updater = SetInterval(self.update_interval, self.progress)
            await self._upload_process()
        except Exception as err:
            if isinstance(err, RetryError):
                LOGGER.info(f"Total Attempts: {err.last_attempt.attempt_number}")
                err = err.last_attempt.exception()
            err = str(err).replace(">", "").replace("<", "")
            LOGGER.error(err)
            await self.listener.on_upload_error(err)
            self._is_errored = True
        finally:
            if self._updater:
                self._updater.cancel()

    async def _upload_process(self):
        if await aiopath.isfile(self._path):
            res = await self.upload_file(self._path)
            if res and res.get("file"):
                link = res["file"]["url"]
                mime_type = "File"
                self.total_files = 1
            else:
                raise ValueError("Failed to upload file to StorageTo")
        elif await aiopath.isdir(self._path):
            collection_id = await self._upload_dir(self._path)
            if collection_id:
                link = f"https://storage.to/c/{collection_id}"
                mime_type = "Folder"
            else:
                raise ValueError("Failed to upload folder to StorageTo")
        else:
            raise ValueError("Invalid file path!")

        if self.listener.is_cancelled:
            return

        LOGGER.info(f"Uploaded To StorageTo: {self.listener.name}")
        await self.listener.on_upload_complete(
            link,
            self.total_files,
            self.total_folders,
            mime_type,
            dir_id="",
        )

    async def cancel_task(self):
        self.listener.is_cancelled = True
        if self.is_uploading:
            LOGGER.info(f"Cancelling StorageTo Upload: {self.listener.name}")
            await self.listener.on_upload_error(
                "StorageTo upload has been cancelled!"
            )
