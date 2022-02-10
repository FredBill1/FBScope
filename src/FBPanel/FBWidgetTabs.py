import tkinter as tk
from tkinter import ttk
from tkinter import simpledialog
from FBWidgetCanvas import *
from FBWidgets import *
from typing import List


class FBWidgetTabs(ttk.Notebook):
    def __init__(self, master, **kw):
        self.canvases: List[FBWidgetCanvas] = []
        super().__init__(master, **kw)
        self.add(ttk.Frame(self), text="<+>")
        self.bind("<ButtonRelease>", self._on_click)

    def _on_click(self, event):
        idx = self.tk.call(self._w, "identify", "tab", event.x, event.y)
        if idx != "":
            if event.num == 1:
                if idx == self.index("end") - 1:
                    self.create()
            elif event.num == 3:
                if idx != self.index("end") - 1:
                    self._rightClick(idx, event)

    def create(self):
        idx = self.index("end") - 1
        name = simpledialog.askstring("输入名称", "输入名称", parent=self)
        if name:
            canvas = FBWidgetCanvas(self, name)
            self.canvases.append(canvas)
            self.insert(idx, canvas, text=name)
            self.select(self.tabs()[idx])

    def _rightClick(self, idx: int, event):
        print(self.toDict())
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="删除", command=lambda idx=idx: self.delete(idx))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def delete(self, idx: int):
        self.forget(idx)
        self.canvases.pop(idx)

    def toDict(self):
        return {"canvases": [canvas.toDict() for canvas in self.canvases]}

    @classmethod
    def fromDict(cls, master, cfg):
        self = cls(master)
        self.forget(0)
        for canvas in cfg["canvases"]:
            cur = FBWidgetCanvas.fromDict(self, canvas)
            self.canvases.append(cur)
            self.add(cur, text=canvas["name"])
        self.add(ttk.Frame(self), text="<+>")
        return self
