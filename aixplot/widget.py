# Copyright (c) 2019 Lukas Koschmieder

import asyncio
from ipywidgets import Box, Dropdown, HBox, Label, Layout, \
                       link, Output, Text, ToggleButtons, VBox
import logging
import time
from traitlets import Bool, HasTraits, observe, Unicode

from .logging import OutputWidgetHandler
from .plotter import Plotter

module_logger = logging.getLogger(__name__)
module_logger.setLevel(logging.INFO)
module_logger.addHandler(logging.StreamHandler())

class Widget(Box):
    x, y = Unicode(), Unicode()
    read, refresh = Bool(True), Bool(True)

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

        ui_x = Dropdown(options=labels, value=self.x)
        ui_y = Dropdown(options=labels, value=self.y)
        ui_read = ToggleButtons(options=[True, False])
        ui_refresh = ToggleButtons(options=[True, False])
        self._progress = Text(disabled=True)
        self._tb = Output()
        self._fig = Output()

        ll = Layout(width="100px", justify_content="flex-end")
        l_x = HBox((Label("x: "),), layout=ll)
        l_y = HBox((Label("y: "),), layout=ll)
        l_read = HBox((Label("Read: "),), layout=ll)
        l_refresh = HBox((Label("Refresh: "),), layout=ll)
        l_progress = HBox((Label("Progress: "),), layout=ll)
        l_tools = HBox((Label("Tools: "),), layout=ll)

        self.observe(self._on_change_xy, names=['x','y'])
        self.observe(self._on_change_read, names=['read'])
        link((self, 'x'), (ui_x, 'value'))
        link((self, 'y'), (ui_y, 'value'))
        link((self, 'read'), (ui_read, 'value'))
        link((self, 'refresh'), (ui_refresh, 'value'))

        b = (HBox((l_x, ui_x)),
             HBox((l_y, ui_y)),
             HBox((l_read, ui_read)),
             HBox((l_progress, self._progress)),
             HBox((l_refresh, ui_refresh)),
             HBox((l_tools, self._tb)),
             self._fig)

        self._ui = (ui_x, ui_y, ui_read, ui_refresh)

        self._plot, self._task, self._last_update = None, None, 0
        read = self.read; self.read = False; self.read = read
        super(self.__class__, self).__init__((VBox(b),))

    def _on_change_read(self, b):
        if not self._plot:
            self._display_plot()
        self._read(b.new)
    def _on_change_xy(self, b):
        self._refresh_plot(self._cacher.cache)
    def _on_update(self, cache, new):
        if self.refresh: self._refresh_plot(cache, new)
        updates = int(1.0 / (time.time() - self._last_update))
        self._progress.value = "{} | {} updates/s".format(
            len(cache[self.x]), updates)
        self._last_update = time.time()
    def _on_eof(self, cache):
        self._progress.value = "{} | EOF".format(len(cache[self.x]))

    def _set_disable_ui(self, b):
        for i in self._ui: i.disabled = b

    def disable_ui(func):
        def deco(self, *args, **kwargs):
            self._set_disable_ui(True)
            func(self, *args, **kwargs)
            self._set_disable_ui(False)
        return deco

    def _refresh_plot(self, cache, new=None):
        self._plotter.refresh(self.x, self.y, cache, new)

    @disable_ui
    def _read(self, b):
        if b and not self._task:
            p, c = self._plotter, self._cacher
            coro = c.async_cache(stop_cond=False, on_update=self._on_update,
                                 on_eof=self._on_eof)
            self.logger.debug("%s", coro)
            self._task = asyncio.ensure_future(coro)
        else:
            if self._task: self._task.cancel()
            self._task = None

    @disable_ui
    def _display_plot(self):
        p, x, y = self._plotter, self.x, self.y
        self.logger.debug("Plot x=%s y=%s", x, y)
        plot = p.plot(x, y)
        if not self._plot:
            with self._fig: display(plot.figure)
            with self._tb: display(plot.toolbar)
            self._plot = plot
