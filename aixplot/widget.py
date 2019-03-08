# Copyright (c) 2019 Lukas Koschmieder

from abc import ABC, abstractmethod
import asyncio
from ipywidgets import Box, Checkbox, Dropdown, HBox, Label, Layout, \
                       link, Output, Text, ToggleButton, ToggleButtons, VBox
import logging
import time
from traitlets import Bool, HasTraits, Instance, List, observe, Unicode

from .logging import OutputWidgetHandler
from .plotter import Plotter

module_logger = logging.getLogger(__name__)
module_logger.setLevel(logging.INFO)
#module_logger.addHandler(logging.StreamHandler())

class Filter(ABC):
    @abstractmethod
    def __repr__(self):
        pass
    @abstractmethod
    def __call__(self, label, cache):
        pass

class NoneFilter(Filter):
    def __repr__(self):
        return "None"
    def __call__(self, label, cache):
        return cache[label]

class Widget(Box):
    x, y = Unicode(), Unicode()
    read, refresh = Bool(True), Bool(True)
    filter = Instance(klass=Filter, allow_none=True)
    filters = List([NoneFilter()])

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

        self.filter = self.filter if self.filter else self.filters[0]

        ui_x = Dropdown(description="x:", options=labels, value=self.x)
        ui_y = Dropdown(description="y:", options=labels, value=self.y)
        ui_read = ToggleButton(description="Read")
        ui_refresh = ToggleButton(description="Plot")
        ui_filter = Dropdown(description="Filters:",
                             options=self.filters, value=self.filter)
        self._tb = Output(layout={"padding":"0","margin":"0"})
        self._fig = Output(layout={"padding":"0","margin":"0"})

        self.observe(self._on_change_xy, names=['x','y','filter'])
        self.observe(self._on_change_read, names=['read'])
        link((self, 'x'), (ui_x, 'value'))
        link((self, 'y'), (ui_y, 'value'))
        link((self, 'read'), (ui_read, 'value'))
        link((self, 'refresh'), (ui_refresh, 'value'))
        link((self, 'filter'), (ui_filter, 'value'))

        l = Layout(display="inline-flex", flex_flow="row wrap")
        b = (HBox((ui_x, ui_y, ui_filter,), layout=l),
             HBox((ui_read, ui_refresh, self._tb,), layout=l),
             self._fig,
             HBox((log_handler.out,), layout=l))

        self._ui = (ui_x, ui_y, ui_read, ui_refresh, ui_filter)

        self._plot, self._task, self._last_update = None, None, 0
        read = self.read; self.read = False; self.read = read
        super(Widget, self).__init__((VBox(b),))

    def _on_change_read(self, b):
        if not self._plot: self._display_plot()
        self._read(b.new)

    def _on_change_xy(self, b):
        self._refresh_plot()

    def _on_update(self, cache, new):
        if self.refresh: self._refresh_plot()
        updates = int(1.0 / (time.time() - self._last_update))
        progress = "{} | {} updates/s" if updates > 0 else "{}"
        x = progress.format(len(cache[self.x]), updates)
        self.logger.info(x)
        self._last_update = time.time()

    def _on_eof(self, cache):
        x = "{} | EOF".format(len(cache[self.x]))
        self.logger.info(x)

    def _set_disable_ui(self, b):
        for i in self._ui: i.disabled = b

    def disable_ui(func):
        def deco(self, *args, **kwargs):
            self._set_disable_ui(True)
            func(self, *args, **kwargs)
            self._set_disable_ui(False)
        return deco

    def _refresh_plot(self):
        self._plotter.refresh(self.x, self.y, self.filter)

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
        plot = p.plot(x, y)
        if not self._plot:
            with self._fig: display(plot.figure)
            with self._tb: display(plot.toolbar)
            self._plot = plot
