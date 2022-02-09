from typing import List, Callable
import tkinter as tk
from tkinter import ttk, dnd
from utils import *


class DNDBase:
    def __init__(self):
        self.canvas: tk.Canvas = None
        self.frame: ttk.Label = None
        self.dndid = None
        self._dragable: bool = False

    @property
    def dragable(self):
        return self._dragable

    @dragable.setter
    def dragable(self, value):
        if self._dragable == value:
            return
        self._dragable = value
        recursiveSetState(self.frame, value)

    def _on_drag(self, event):
        if self._dragable and dnd.dnd_start(self, event):
            self.x_off, self.y_off = event.x, event.y
            self.x_orig, self.y_orig = self.canvas.coords(self.dndid)

    def attach(self, canvas: tk.Canvas, x: int = 10, y: int = 10) -> None:
        if canvas is self.canvas:
            self.canvas.coords(self.dndid, x, y)
            return
        if self.canvas:
            self.detach()
        if not canvas:
            return
        self.canvas = canvas
        self.frame = ttk.Label(canvas)
        self.construct(self.frame)
        self.afterConstruct()
        self.configureAll(lambda w: w.bind("<ButtonPress-1>", self._on_drag))
        self.dndid = canvas.create_window(x, y, window=self.frame, anchor="nw")
        self.registerCanvas(canvas)

    def configureAll(self, func: Callable[[tk.Widget], None]) -> None:
        recursiveConfigure(self.frame, func)

    def registerCanvas(self, canvas: tk.Canvas) -> None:
        ...

    def unregisterCanvas(self, canvas: tk.Canvas) -> None:
        ...

    def detach(self) -> None:
        if not self.canvas:
            return
        self.unregisterCanvas(self.canvas)
        self.canvas.delete(self.dndid)
        self.frame.destroy()
        self.canvas = self.frame = self.dndid = None

    def construct(self, frame: ttk.LabelFrame) -> None:
        raise NotImplementedError()

    def afterConstruct(self) -> None:
        ...

    def pos(self):
        return self.canvas.coords(self.dndid)

    def move(self, event):
        x, y = self.where(self.canvas, event)
        self.canvas.coords(self.dndid, x, y)

    def putback(self):
        self.canvas.coords(self.dndid, self.x_orig, self.y_orig)

    def where(self, canvas, event):
        # where the corner of the canvas is relative to the screen:
        x_org = canvas.winfo_rootx()
        y_org = canvas.winfo_rooty()
        # where the pointer is relative to the canvas widget:
        x = event.x_root - x_org
        y = event.y_root - y_org
        # compensate for initial pointer offset
        return x - self.x_off, y - self.y_off

    def dnd_end(self, target, event):
        ...


class DNDCanvas(tk.Canvas):
    def dnd_accept(self, source, event):
        return self

    def dnd_enter(self, source, event):
        self.focus_set()  # Show highlight border
        x, y = source.where(self, event)
        x1, y1, x2, y2 = source.canvas.bbox(source.dndid)
        dx, dy = x2 - x1, y2 - y1
        self.dndid = self.create_rectangle(x, y, x + dx, y + dy)
        self.dnd_motion(source, event)

    def dnd_motion(self, source: DNDBase, event):
        x, y = source.where(self, event)
        x1, y1, x2, y2 = self.bbox(self.dndid)
        self.move(self.dndid, x - x1, y - y1)

    def dnd_leave(self, source, event):
        self.focus_set()  # Hide highlight border
        self.delete(self.dndid)
        self.dndid = None

    def dnd_commit(self, source, event):
        self.dnd_leave(source, event)
        x, y = source.where(self, event)
        source.attach(self, x, y)


__all__ = ["DNDBase", "DNDCanvas"]

