# This file is a part of NEO-WZML (github.com/irisXDR/NEO-WZML)

from time import time

from bot import LOGGER
from bot.helper.ext_utils.status_utils import (
    get_readable_file_size,
    EngineStatus,
    MirrorStatus,
    get_readable_time,
)


class MergeStatus:
    def __init__(self, listener, obj, gid, group=0, total=0):
        self.listener = listener
        self._obj = obj
        self._gid = gid
        self._start_time = time()
        self.engine = EngineStatus().STATUS_FFMPEG
        self._group = group
        self._total = total

    def gid(self):
        return self._gid

    def progress(self):
        try:
            return f"{min(self._obj.processed_bytes / self.listener.size * 100, 100):.2f}%"
        except ZeroDivisionError:
            return "0%"

    def speed(self):
        try:
            return f"{get_readable_file_size(self._obj.processed_bytes / (time() - self._start_time))}/s"
        except ZeroDivisionError:
            return "0B/s"

    def processed_bytes(self):
        return get_readable_file_size(self._obj.processed_bytes)

    def name(self):
        return f"Video Merge ({self._group}/{self._total}): {self.listener.name}" if self._total else self.listener.name

    def size(self):
        return get_readable_file_size(self.listener.size)

    def eta(self):
        try:
            remaining = (self.listener.size - self._obj.processed_bytes) / (self._obj.processed_bytes / (time() - self._start_time))
            return get_readable_time(remaining)
        except (ZeroDivisionError, OverflowError):
            return "-"

    def status(self):
        return MirrorStatus.STATUS_MERGING

    def task(self):
        return self

    async def cancel_task(self):
        LOGGER.info(f"Cancelling Merge: {self.listener.name}")
        self.listener.is_cancelled = True
        if (
            self.listener.subproc is not None
            and self.listener.subproc.returncode is None
        ):
            try:
                self.listener.subproc.kill()
            except Exception:
                pass
        await self.listener.on_upload_error("Merge stopped by user!")


class AdvancedMergeStatus:
    def __init__(self, listener, gid):
        self.listener = listener
        self._gid = gid
        self.engine = EngineStatus().STATUS_FFMPEG

    def gid(self):
        return self._gid

    def progress(self):
        return "0%"

    def speed(self):
        return "0B/s"

    def processed_bytes(self):
        return "0B"

    def name(self):
        return self.listener.name

    def size(self):
        return get_readable_file_size(self.listener.size)

    def eta(self):
        return "-"

    def status(self):
        return MirrorStatus.STATUS_WAITING

    def task(self):
        return self

    async def cancel_task(self):
        LOGGER.info(f"Cancelling Advanced Merge Wait: {self.listener.name}")
        self.listener.is_cancelled = True
        from web.advanced_merge_store import delete_state
        from bot.modules.advanced_merge import _pending
        delete_state(self._gid)
        if pending := _pending.get(self._gid):
            _, done = pending
            done.set()
        await self.listener.on_upload_error("Advanced merge stopped by user!")


class SyncStreamsStatus:
    def __init__(self, listener, gid):
        self.listener = listener
        self._gid = gid
        self.engine = EngineStatus().STATUS_MKVMERGE

    def gid(self):
        return self._gid

    def progress(self):
        return "0%"

    def speed(self):
        return "0B/s"

    def processed_bytes(self):
        return "0B"

    def name(self):
        return self.listener.name

    def size(self):
        return get_readable_file_size(self.listener.size)

    def eta(self):
        return "-"

    def status(self):
        return MirrorStatus.STATUS_WAITING

    def task(self):
        return self

    async def cancel_task(self):
        LOGGER.info(f"Cancelling Sync Streams Wait: {self.listener.name}")
        self.listener.is_cancelled = True
        from web.sync_streams_store import delete_state
        from bot.modules.sync_streams import _pending
        delete_state(self._gid)
        if pending := _pending.get(self._gid):
            _, done = pending
            done.set()
        await self.listener.on_upload_error("Sync audio/subtitles stopped by user!")


class SyncStreamsProcessingStatus:
    def __init__(self, listener, obj, gid, group=0, total=0):
        self.listener = listener
        self._obj = obj
        self._gid = gid
        self._start_time = time()
        self.engine = EngineStatus().STATUS_MKVMERGE
        self._group = group
        self._total = total

    def gid(self):
        return self._gid

    def progress(self):
        try:
            return f"{min(self._obj.processed_bytes / self.listener.size * 100, 100):.2f}%"
        except ZeroDivisionError:
            return "0%"

    def speed(self):
        try:
            return f"{get_readable_file_size(self._obj.processed_bytes / (time() - self._start_time))}/s"
        except ZeroDivisionError:
            return "0B/s"

    def processed_bytes(self):
        return get_readable_file_size(self._obj.processed_bytes)

    def name(self):
        return f"Sync Streams ({self._group}/{self._total}): {self.listener.name}" if self._total else self.listener.name

    def size(self):
        return get_readable_file_size(self.listener.size)

    def eta(self):
        try:
            remaining = (self.listener.size - self._obj.processed_bytes) / (self._obj.processed_bytes / (time() - self._start_time))
            return get_readable_time(remaining)
        except (ZeroDivisionError, OverflowError):
            return "-"

    def status(self):
        return MirrorStatus.STATUS_SYNC_STREAMS

    def task(self):
        return self

    async def cancel_task(self):
        LOGGER.info(f"Cancelling Sync Streams: {self.listener.name}")
        self.listener.is_cancelled = True
        if (
            self.listener.subproc is not None
            and self.listener.subproc.returncode is None
        ):
            try:
                self.listener.subproc.kill()
            except Exception:
                pass
        await self.listener.on_upload_error("Sync audio/subtitles stopped by user!")
