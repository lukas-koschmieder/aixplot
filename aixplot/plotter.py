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
    def close(self):
        self.figure.close()
        self.toolbar.close()

class Plotter(object):
    def __init__(self, cacher, logger=None):
        self.cacher = cacher
        self.logger = logger if logger else module_logger
        self._plot = None

    def refresh(self, x, y, filter=None):
        if self._plot:
            fig = self._plot.figure
            c = self.cacher.cache
            dx, dy = None, None
            if filter:
                dx, dy = filter(x, c), filter(y, c)
            else:
                dx, dy = c[x], c[y]
            m, a = fig.marks, fig.axes
            m[0].x, m[0].y = dx, dy
            a[0].label, a[1].label = x, y

    def plot(self, x, y, xscale=None, yscale=None):
        if not self._plot:
            xscale = xscale if xscale else LinearScale()
            yscale = yscale if yscale else LinearScale()
            a = [Axis(label=x, scale=xscale),
                 Axis(label=y, scale=yscale, side='left')]
            m = Lines(x=[], y=[], scales={'x': xscale, 'y': yscale})
            p = Plot(Figure(marks=[m], axes=a,
                            fig_margin=dict(top=10, bottom=40,
                                            left=60, right=0)))
            self._plot = p
        self.refresh(x, y)
        return self._plot
