from typing import List, Dict, Set, Callable, TYPE_CHECKING
import tkinter as tk
from tkinter import ttk
from DND import *
from utils import *
from collections import defaultdict
from tkinter import simpledialog, messagebox
from FBWidgets import FBWidget, FBWIDGET_DICT


class FBWidgetCanvas(DNDCanvas):
    def __init__(self, master, **kw):
        super().__init__(master, kw)

        self.editing = False
        self.widgets: Dict[str, "FBWidget"] = {}
        self.callbacks: Dict[str, Dict[str, Set[str]]] = defaultdict(lambda: defaultdict(set))

        self.create_menu = tk.Menu(tearoff=0)
        for wid_type in FBWIDGET_DICT.keys():
            self.create_menu.add_command(label=wid_type, command=lambda wid=wid_type: self.createWidgetByType(wid))
        self.bind("<Button-3>", self._rightClick)

    def createWidgetByType(self, wid_type: str):
        name = simpledialog.askstring("输入名称", "请输入名称", initialvalue=f"新组件{len(self.widgets)+1}", parent=self)
        if name:
            if name in self.widgets:
                messagebox.showerror("组件名称已存在", "组件名称已存在", parent=self)
                return None
            cur = FBWIDGET_DICT[wid_type](name)
            cur.attach(self, *self._click_pos)
            cur.dragable = self.editing
            return cur

    def createWidgetByDict(self, cfg: dict):
        name = cfg.get("name")
        if name in self.widgets:
            messagebox.showerror("组件名称已存在", "组件名称已存在", parent=self)
            return None
        cur = FBWIDGET_DICT[cfg.get("type")].fromDict(cfg, self)
        cur.dragable = self.editing
        return cur

    def _rightClick(self, event):
        self._click_pos = (event.x_root - self.winfo_rootx(), event.y_root - self.winfo_rooty())
        menu = tk.Menu(self, tearoff=0)
        if self.editing:
            menu.add_cascade(label="新建组件", menu=self.create_menu)
            menu.add_separator()
            menu.add_command(label="结束编辑", command=lambda: self.setEditing(False))
        else:
            menu.add_command(label="编辑", command=lambda: self.setEditing(True))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def setEditing(self, editing: bool) -> None:
        if self.editing == editing:
            return
        self.editing = editing
        for widget in self.widgets.values():
            widget.dragable = editing

    def _callback(self, name: str, event: str) -> None:
        print(name, event)
        if name in self.callbacks and event in self.callbacks[name]:
            print(self.callbacks[name][event])

    @staticmethod
    def registerCallback(name: str, event: str, callback: str) -> None:
        FBWidgetCanvas.callbacks[name][event].add(callback)

    @staticmethod
    def unregisterCallback(name: str, event: str, callback: str) -> None:
        FBWidgetCanvas.callbacks[name][event].remove(callback)


__all__ = ["FBWidgetCanvas"]

