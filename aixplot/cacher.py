# Copyright (c) 2019 Lukas Koschmieder

from abc import ABC, abstractmethod, abstractstaticmethod
import asyncio
from collections import defaultdict
import logging

module_logger = logging.getLogger(__name__)
module_logger.setLevel(logging.INFO)
module_logger.addHandler(logging.StreamHandler())

class Cacher(ABC):
    def __init__(self, file, logger=None):
        self._file = file
        self.logger = logger if logger else module_logger
        self.cache = defaultdict(list)

    @abstractmethod
    def _filter(self, data, cache):
        pass

    @abstractmethod
    async def _async_read(self):
        pass

    async def async_cache(self, stop_cond=None,
                          on_stop=None, on_update=None, on_eof=None):
        while True:
            await asyncio.sleep(0)
            new = await self._async_read(self._file)
            if new:
                self._filter(new, self.cache)
                if on_update: on_update(self.cache, new)
            else:
                if on_eof: on_eof(self.cache)
            if stop_cond and stop_cond(self.cache):
                if on_stop: on_stop(self.cache)
                return self.cache
