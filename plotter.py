# Copyright (c) 2019 Lukas Koschmieder

import asyncio
from bqplot import Axis, Figure, LinearScale, Lines
import logging

module_logger = logging.getLogger(__name__)
module_logger.setLevel(logging.INFO)
module_logger.addHandler(logging.StreamHandler())

class Plotter(object):
    def __init__(self, cacher, logger=None):
        self.cacher = cacher
        self.logger = logger if logger else module_logger
        self._x, self._y, self._marks = None, None, None

    def refresh(self, cache, new=None):
        if self._marks:
            self._marks.x = cache[self._x]
            self._marks.y = cache[self._y]

    def plot(self, x, y, title="", xscale=None, yscale=None):
        xscale = xscale if xscale else LinearScale()
        yscale = yscale if yscale else LinearScale()
        a = [Axis(label=x, scale=xscale),
             Axis(label=y, scale=yscale, side='left')]
        m = Lines(x=[], y=[], scales={'x': xscale, 'y': yscale})
        fig = Figure(marks=[m], axes=a, title=title)
        self._x, self._y, self._marks = x, y, m
        return fig
