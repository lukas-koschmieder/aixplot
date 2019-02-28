# Copyright (c) 2019 Lukas Koschmieder

import asyncio
from bqplot import Axis, Figure, LinearScale, Lines, Toolbar
from ipywidgets import Label, HBox, VBox
import logging

module_logger = logging.getLogger(__name__)
module_logger.setLevel(logging.INFO)
module_logger.addHandler(logging.StreamHandler())

class Plot(VBox):
    def __init__(self, figure):
        self.figure = figure
        self.toolbar = Toolbar(figure=figure)
        super(self.__class__, self).__init__((self.figure, self.toolbar))

class Plotter(object):
    def __init__(self, cacher, logger=None):
        self.cacher = cacher
        self.logger = logger if logger else module_logger
        self._plot = None

    def refresh(self, x, y, cache, new=None):
        if self._plot:
            self._plot.figure.marks[0].x = cache[x]
            self._plot.figure.marks[0].y = cache[y]
            self._plot.figure.axes[0].label = x
            self._plot.figure.axes[1].label = y

    def plot(self, x, y, title="", xscale=None, yscale=None):
        if not self._plot:
            xscale = xscale if xscale else LinearScale()
            yscale = yscale if yscale else LinearScale()
            a = [Axis(label=x, scale=xscale),
                 Axis(label=y, scale=yscale, side='left')]
            m = Lines(x=[], y=[], scales={'x': xscale, 'y': yscale})
            p = Plot(Figure(marks=[m], axes=a, title=title))
            self._plot = p
        self.refresh(x, y, self.cacher.cache)
        return self._plot
