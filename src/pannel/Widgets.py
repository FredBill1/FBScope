from typing import List, Dict, Set, Callable
import tkinter as tk
from tkinter import ttk
from DND import *
from utils import *
from collections import defaultdict
from tkinter import simpledialog, messagebox


class FBWidget(DNDBase):
    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self.data: Dict[str, tk.Variable] = {}
        self.config: Dict[str, str] = {}

    def registerCanvas(self, canvas: "FBWidgetCanvas") -> None:
        if self.name in canvas.widgets:
            raise ValueError("Widget name already exists")
        canvas.widgets[self.name] = self

    def unregisterCanvas(self, canvas: "FBWidgetCanvas") -> None:
        canvas.widgets.pop(self.name, None)

    def _callback(self, event: str) -> None:
        self.canvas._callback(self.name, event)

    def rename(self):
        name = simpledialog.askstring("输入名称", "请输入名称", initialvalue=self.name, parent=self.frame)
        if name:
            if name == self.name:
                return
            if name in self.canvas.widgets:
                messagebox.showerror("组件名称已存在", "组件名称已存在", parent=self.frame)
                return
            self.canvas.widgets[name] = self
            del self.canvas.widgets[self.name]
            self.name = name

    def afterConstruct(self):
        self.configureAll(lambda w: w.bind("<Button-3>", self._rightClick))

    def _rightClick(self, event):
        if not self._dragable:
            return
        menu = tk.Menu(self.frame, tearoff=0)
        menu.add_command(label="重命名", command=self.rename)
        menu.add_command(label="删除", command=self.detach)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()


class FBWidgetCanvas(DNDCanvas):
    def __init__(self, master, **kw):
        super().__init__(master, kw)

        self.editing = False
        self.widgets: Dict[str, "FBWidget"] = {}
        self.callbacks: Dict[str, Dict[str, Set[str]]] = defaultdict(lambda: defaultdict(set))

        self.create_menu = tk.Menu(tearoff=0)
        for widgetType in WIDGTET_CLASSES:
            self.create_menu.add_command(
                label=widgetType.__name__, command=lambda wid=widgetType: self.createWidget(wid)
            )
        self.bind("<Button-3>", self._rightClick)

    def createWidget(self, type: Callable[[str], FBWidget]):
        print(type.__name__)
        name = simpledialog.askstring("输入名称", "请输入名称", initialvalue=f"新组件{len(self.widgets)+1}", parent=self)
        if name:
            if name in self.widgets:
                messagebox.showerror("组件名称已存在", "组件名称已存在", parent=self)
                return
            cur = type(name)
            cur.attach(self, *self._click_pos)
            cur.dragable = self.editing

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


class FBButton(FBWidget):
    def construct(self, frame: ttk.LabelFrame) -> None:
        self.button = ttk.Button(frame, text=self.name, command=lambda: (frame.focus_set(), self._callback("click")))
        self.button.pack(fill="both", expand=True)

    def rename(self):
        super().rename()
        self.button["text"] = self.name


class FBEntry(FBWidget):
    def construct(self, frame: ttk.LabelFrame) -> None:
        self.data["text"] = tk.StringVar(frame)
        self.label = ttk.Label(frame, text=self.name)
        self.entry = ttk.Entry(frame, textvariable=self.data["text"])
        self.entry.bind("<Return>", lambda _: (frame.focus_set(), self._callback("enter")))
        self.label.pack(side="left")
        self.entry.pack(side="left")

    def rename(self):
        super().rename()
        self.label["text"] = self.name


WIDGTET_CLASSES = [FBButton, FBEntry]


if __name__ == "__main__":
    from ttkbootstrap import Style

    class Test(FBWidget):
        def construct(self, frame: ttk.LabelFrame):
            self.button = ttk.Button(frame, text="asfd", command=lambda: print("asdf"))
            self.button.pack(padx=10, pady=10)

    style = Style(theme="cosmo")
    root = style.master
    btns = ttk.Frame(root, padding=10)
    btns.pack()
    t1 = FBWidgetCanvas(root)
    t1.pack()
    ttk.Button(btns, command=root.quit, text="退出").pack(side="left", padx=10, pady=10)
    ttk.Button(btns, command=lambda: t1.setEditing(True), text="开启编辑").pack(side="left", padx=10, pady=10)
    ttk.Button(btns, command=lambda: t1.setEditing(False), text="关闭编辑").pack(side="left", padx=10, pady=10)
    w1 = FBButton("w1")
    w1.attach(t1)
    root.mainloop()
