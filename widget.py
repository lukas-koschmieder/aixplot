# Copyright (c) 2019 Lukas Koschmieder

import asyncio
from ipywidgets import Box, Dropdown, HBox, Label, Layout, \
                       link, Output, ToggleButtons, VBox
import logging
from traitlets import Bool, HasTraits, observe, Unicode

from .logging import OutputWidgetHandler
from .plotter import Plotter

module_logger = logging.getLogger(__name__)
module_logger.setLevel(logging.INFO)
module_logger.addHandler(logging.StreamHandler())

class Widget(Box):
    x, y = Unicode(), Unicode()
    plot = Bool(True)

    def __init__(self, cacher, logger=None, **traits):
        self._cacher = cacher
        self.logger = logger if logger else module_logger
        HasTraits.__init__(self, **traits)

        log_handler = OutputWidgetHandler()
        fmt = '%(asctime)s  [%(levelname)s] %(message)s'
        log_handler.setFormatter(logging.Formatter(fmt))
        self.logger.addHandler(log_handler)

        self._plotter = Plotter(cacher, logger=self.logger)

        labels = cacher.labels()
        self.x = self.x if self.x else labels[0]
        self.y = self.y if self.y else labels[0]
        ui_x = Dropdown(options=labels, description='x:', value=self.x)
        ui_y = Dropdown(options=labels, description='y:', value=self.y)
        ui_onoff = ToggleButtons(description='Plot:', options=[True, False])
        self._ui = (ui_x, ui_y, ui_onoff)
        self._status = Label()
        self._fig_out = Output()

        self.observe(self._on_change_xy, names=['x','y'])
        self.observe(self._on_change_onoff, names=['plot'])
        link((self, 'x'), (ui_x, 'value'))
        link((self, 'y'), (ui_y, 'value'))
        link((self, 'plot'), (ui_onoff, 'value'))

        left = Layout(display='flex', flex_flow='row wrap')
        b = (HBox((ui_x, ui_y,), layout=left),)\
            + (HBox((ui_onoff, self._status,), layout=left),)\
            + (self._fig_out,)\
            + (HBox((log_handler.out,),),)

        self._fig, self._task = None, None
        plot = self.plot; self.plot = False; self.plot = plot
        super(self.__class__, self).__init__((VBox(b),))

    def _on_change_onoff(self, b):
        if not self._fig:
            self._display_fig()
        self._plot(b.new)
    def _on_change_xy(self, b):
        self._display_fig()
        self._refresh_plot(self._cacher.cache)

    def _set_disable_ui(self, b):
        for i in self._ui: i.disabled = b

    def disable_ui(func):
        def deco(self, *args, **kwargs):
            self._set_disable_ui(True)
            func(self, *args, **kwargs)
            self._set_disable_ui(False)
        return deco

    def _refresh_plot(self, cache, new=None):
        self._plotter.refresh(cache, new)

    def _on_update(self, cache, new):
        self._refresh_plot(cache, new)
        self._status.value = "Progress:  {}".format(len(cache[self.x]))

    def _on_eof(self, cache):
        self._refresh_plot(cache)
        self._status.value = "Progress:  {} | EOF".format(len(cache[self.x]))

    @disable_ui
    def _plot(self, b):
        if b and not self._task:
            self.logger.debug("Start")
            p, c = self._plotter, self._cacher
            coro = c.async_cache(stop_cond=False, on_update=self._on_update,
                                 on_eof=self._on_eof)
            self.logger.debug("%s", coro)
            self._task = asyncio.ensure_future(coro)
        else:
            self.logger.debug("Pause")
            if self._task: self._task.cancel()
            self._task = None

    @disable_ui
    def _display_fig(self):
        p, x, y = self._plotter, self.x, self.y
        self.logger.debug("Plot x=%s y=%s", x, y)
        fig = p.plot(x, y)
        with self._fig_out: display(fig)
        if self._fig: self._fig.close()
        self._fig = fig
