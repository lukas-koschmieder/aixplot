# Copyright (c) 2019 Lukas Koschmieder

from abc import ABC, abstractmethod
import asyncio

class Reader(ABC):
    def __init__(self):
        self._fpos = 0

    @abstractmethod
    def _process_line(self, line):
        pass

    async def async_read(self, file, tries=3, sleep=1.0, on_done=None):
        t = tries
        while t > 0:
            file.seek(self._fpos)
            self._fpos = file.tell()
            line = file.readline()
            if line:
                t = tries
                self._fpos = file.tell()
                data = self._process_line(line)
                if data:
                    if on_done: on_done(data)
                    return data
            else:
                t = t - 1
                await asyncio.sleep(sleep)
        return None
