# Copyright (c) 2019 Lukas Koschmieder

from abc import ABC, abstractmethod
import asyncio
from ipywidgets import Box, Button, Checkbox, Dropdown, HBox, Label, Layout, \
                       link, Output, Text, VBox
import logging
import time
from traitlets import Bool, HasTraits, Instance, List, observe, Unicode

from .cacher import Cacher
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
    x, y, filename = Unicode(), Unicode(), Unicode()
    read, refresh = Bool(True), Bool(True)
    filters = List([NoneFilter()])
    filter = Instance(klass=Filter, allow_none=True)

    def __init__(self, cacher_class, logger=None, **traits):
        self._cacher_class = cacher_class
        self.logger = logger if logger else module_logger
        self._plot, self._task, self._file  = None, None, None
        self._last_update = 0
        HasTraits.__init__(self, **traits)

        log_handler = OutputWidgetHandler()
        fmt = '%(asctime)s [%(levelname)s] %(message)s'
        log_handler.setFormatter(logging.Formatter(fmt, "%H:%M:%S"))
        self.logger.addHandler(log_handler)

        labels = self._cacher_class.labels(self)
        self.x = self.x if self.x else labels[0]
        self.y = self.y if self.y else labels[0]
        self.filter = self.filter if self.filter else self.filters[0]
        self.read, self.refresh = False, False

        ui_filename = Text(description="File:", layout={"flex":"1 0 auto"})
        ui_x = Dropdown(description="x:", options=labels)
        ui_y = Dropdown(description="y:", options=labels)
        ui_read = Button(description="Read")
        ui_cancel = Button(description="Cancel")
        ui_refresh = Checkbox(description="Refresh plot", layout={"width":"auto"},
            tooltip="Automatically update plot when new data is read")
        ui_filter = Dropdown(description="Filters:", options=self.filters)
        self._tb = Output(layout={"padding":"0","margin":"0","flex":"1 0 auto"})
        self._fig = Output(layout={"padding":"0","margin":"0"})
        spacer = Box(layout={"flex":"0 0 90px"})
        ui_log = Dropdown(description="Log level:", value="INFO",
                          options=["ERROR", "WARNING", "INFO", "DEBUG"])

        ui_read.on_click(self._read)
        ui_cancel.on_click(self._cancel)
        self.observe(self._refresh_plot, names=['x','y','filter'])
        self.observe(self._read, names=['read'])
        ui_log.observe(self._update_log, names=['value'])
        link((self, 'filename'), (ui_filename, 'value'))
        link((self, 'x'), (ui_x, 'value'))
        link((self, 'y'), (ui_y, 'value'))
        link((self, 'refresh'), (ui_refresh, 'value'))
        link((self, 'filter'), (ui_filter, 'value'))

        l1 = Layout(display="inline-flex", flex_flow="row wrap")
        l2 = Layout(display="inline-flex", flex_flow="row wrap",
                    justify_content="space-between")
        b = (HBox((ui_filename, ui_read, ui_cancel,), layout=l1),
             HBox((ui_x, ui_y, ui_filter,), layout=l1),
             HBox((spacer, self._tb, ui_refresh,), layout=l2),
             HBox((self._fig,), layout=l1),
             HBox((ui_log,), layout=l1),
             HBox((log_handler.out,), layout=l1),)

        self._ui = (ui_filename, ui_x, ui_y, ui_read, ui_cancel,
                    ui_refresh, ui_filter)

        self.refresh = True
        self._read()
        super(Widget, self).__init__((VBox(b),))

    def _set_disable_ui(self, b):
        for i in self._ui: i.disabled = b
    def disable_ui(func):
        def deco(self, *args, **kwargs):
            self._set_disable_ui(True)
            func(self, *args, **kwargs)
            self._set_disable_ui(False)
        return deco

    @disable_ui
    def _read(self, b=None):
        self._cancel_task()
        try:
            if self._create_plotter():
                self._display_plot()
            self._start_task()
        except Exception as e:
            self.logger.error(e)

    @disable_ui
    def _cancel(self, b=None):
        self._cancel_task()

    @disable_ui
    def _update_log(self, b):
        self.logger.setLevel(getattr(logging, b.new))

    def _create_plotter(self):
        if self._file and self._file.name == self.filename:
            self.logger.debug("File is already open")
            return False

        self._file = open(self.filename)
        self.logger.info("File opened: %s", self.filename)
        self._cacher = self._cacher_class(self._file, self.logger)
        self._plotter = Plotter(self._cacher, self.logger)
        return True

    def _display_plot(self):
        plot = self._plotter.plot(self.x, self.y)
        if self._plot: self._plot.close()
        self._plot = plot
        with self._fig: display(plot.figure)
        with self._tb: display(plot.toolbar)

    def _refresh_plot(self, b=None):
        if self._plotter:
            self._plotter.refresh(self.x, self.y, self.filter)

    def _start_task(self):
        p, c = self._plotter, self._cacher
        coro = c.async_cache(stop_cond=False, on_update=self._on_update,
                             on_eof=self._on_eof)
        self._task = asyncio.ensure_future(coro)

    def _cancel_task(self):
        if self._task: self._task.cancel()
        self._task = None

    def _on_update(self, cache, new):
        if self.refresh: self._refresh_plot()
        updates = int(1.0 / (time.time() - self._last_update))
        progress = "{} | {} updates/s" if updates > 0 else "{}"
        self.logger.debug(progress.format(len(cache[self.x]), updates))
        self._last_update = time.time()

    def _on_eof(self, cache):
        self.logger.debug("{} | EOF".format(len(cache[self.x])))
