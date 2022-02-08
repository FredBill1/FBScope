from typing import List, Dict
import tkinter as tk
from tkinter import ttk
from DND import *
from utils import *


class Widget(DNDBase):
    Widgets: Dict[str, "Widget"] = {}
    _editing: bool = False

    @staticmethod
    def setEditing(value: bool) -> None:
        if Widget._editing == value:
            return
        Widget._editing = value
        for widget in Widget.Widgets.values():
            recursiveSetState(widget.frame, value)

    def __init__(self, name: str):
        super().__init__()
        self.name = name
        if name in self.Widgets:
            raise RuntimeError("Widget name already exists")
        self.Widgets[name] = self

    def __del__(self):
        self.Widgets.pop(self.name, None)


if __name__ == "__main__":
    from ttkbootstrap import Style

    class Test(Widget):
        def construct(self, frame: ttk.LabelFrame):
            self.button = ttk.Button(frame, text="asfd", command=lambda: print("asdf"))
            self.button.pack(padx=10, pady=10)

    style = Style(theme="cosmo")
    root = style.master
    btns = ttk.Frame(root, padding=10)
    btns.pack()
    ttk.Button(btns, command=root.quit, text="退出").pack(side="left", padx=10, pady=10)
    ttk.Button(btns, command=lambda: Widget.setEditing(True), text="开启编辑").pack(side="left", padx=10, pady=10)
    ttk.Button(btns, command=lambda: Widget.setEditing(False), text="关闭编辑").pack(side="left", padx=10, pady=10)
    t1 = DNDCanvas(root)
    t1.pack()
    w1 = Test("w1")
    w1.attach(t1)
    root.mainloop()
