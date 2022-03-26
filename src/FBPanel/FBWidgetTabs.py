import tkinter as tk
import ttkbootstrap as ttk
from tkinter import simpledialog
from tkinter import messagebox
from FBWidgetCanvas import *
from FBWidgets import *
from typing import List


class FBWidgetTabs(ttk.Notebook):
    def __init__(self, uartClient, master, **kw):
        self.canvases: List[FBWidgetCanvas] = []
        super().__init__(master, **kw)
        self._createDummy()
        self.bind("<ButtonRelease>", self._on_click)
        self.bind("<B1-Motion>", self._reorderCB)
        self._isTopmost = False
        self.uartClient = uartClient

    def _createDummy(self):
        cur = tk.Canvas(self)
        cur["background"] = "gray"
        self.add(cur, text="新建")

    def toggleTopmost(self):
        self._isTopmost = not self._isTopmost
        self.master.attributes("-topmost", self._isTopmost)

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
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="重命名", command=lambda: self._askRename(idx))
        menu.add_command(label="复制", command=lambda idx=idx: self.dup(idx))
        menu.add_separator()
        menu.add_command(label="删除", command=lambda idx=idx: self._askDelete(idx))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def dup(self, idx: int):
        cur_config = self.canvases[idx].toDict()
        cur_config["name"] += f"-{len(self.canvases)+1}"
        cur = FBWidgetCanvas.fromDict(self, cur_config)
        self.canvases.insert(idx + 1, cur)
        self.insert(idx + 1, cur, text=cur_config["name"])
        self.select(self.tabs()[idx + 1])

    def delete(self, idx: int):
        self.forget(idx)
        self.canvases.pop(idx)
        self.select(self.tabs()[max(0, idx - 1)])

    def rename(self, idx: int, newName: str):
        self.tab(idx, text=newName)
        self.canvases[idx].name = newName

    def _reorderCB(self, event):
        try:
            new_idx = self.index(f"@{event.x},{event.y}")
            if new_idx < len(self.canvases):
                idx = next(i for i, s in enumerate(self.canvases) if str(s) == self.select())
                if idx != new_idx:
                    self.canvases[idx], self.canvases[new_idx] = self.canvases[new_idx], self.canvases[idx]
                    self.insert(new_idx, child=self.select())
        except tk.TclError:
            pass

    def _askDelete(self, idx: int):
        if messagebox.askokcancel("删除", f"你确定要删除{self.canvases[idx].name}吗? (不可逆)"):
            self.delete(idx)

    def _askRename(self, idx: int):
        name = simpledialog.askstring("输入名称", "输入名称", parent=self)
        if name:
            self.rename(idx, name)

    def toDict(self):
        return {"canvases": self.toList()}

    def toList(self):
        return [canvas.toDict() for canvas in self.canvases]

    @classmethod
    def fromDict(cls, uartClient, master, cfg):
        self = cls(uartClient, master)
        self.forget(0)
        for canvas in cfg["canvases"]:
            cur = FBWidgetCanvas.fromDict(self, canvas)
            self.canvases.append(cur)
            self.add(cur, text=canvas["name"])
        self._createDummy()
        return self


__all__ = ["FBWidgetTabs"]
