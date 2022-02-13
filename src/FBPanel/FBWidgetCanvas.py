from typing import List, Dict, Set, Callable, TYPE_CHECKING, Tuple
import tkinter as tk
from tkinter import ttk
from DND import *
from utils import *
from collections import defaultdict
from tkinter import simpledialog, messagebox
from FBWidgets import FBWidget, FBWIDGET_DICT
from FBWidgetCmdTable import FBWidgetCmdTable

if TYPE_CHECKING:
    from FBWidgetTabs import FBWidgetTabs


class FBWidgetCanvas(DNDCanvas):
    def __init__(self, master: "FBWidgetTabs", name: str, **kw):
        super().__init__(master, kw)
        self.name = name

        self.editing = False
        self.widgets: Dict[str, "FBWidget"] = {}
        self.callbacks: Dict[str, set[str]] = defaultdict(set)

        self.create_menu = tk.Menu(tearoff=0)
        for wid_type in FBWIDGET_DICT.keys():
            self.create_menu.add_command(label=wid_type, command=lambda wid=wid_type: self.createWidgetFromType(wid))
        self.bind("<Button-3>", self._rightClick)
        self.bind("<KeyPress>", self._keyPress)
        self.bind("<KeyRelease>", self._keyRelease)
        self.bind_all("<Escape>", lambda _: self.focus_set())
        self.bind("<Button>", lambda _: self.focus_set())

        self.cmdTable: FBWidgetCmdTable = None
        self.cmdDict: Dict[str, Tuple[str, str]] = {}
        self.cmdList: List[List[str]] = []

        self._pressed = [False] * 26

    def _keyPress(self, event):
        if "a" <= event.char <= "z":
            cur = ord(event.char) - ord("a")
            if not self._pressed[cur]:
                self._pressed[cur] = True
                self._callback(f"<{event.char}>", "press")

    def _keyRelease(self, event):
        if "a" <= event.char <= "z":
            self._pressed[ord(event.char) - ord("a")] = False
            self._callback(f"<{event.char}>", "release")

    def _callback(self, name: str, event: str) -> None:
        cur = f"{name}.{event}"
        if cur in self.callbacks:
            for cmd in self.callbacks[cur]:
                print(cmd)
                res = self._interpreter(cmd)
                print(repr(res))

    def _interpreter(self, cmd: str) -> bytes:
        _, command, variables = (s.strip() for s in cmd.split("$$"))
        if not command:
            return b""

        def getVar(var: List[str]) -> list:
            def getValue(variable: str):
                if variable.startswith("("):
                    if not variable.endswith(")"):
                        messagebox.showerror("错误的变量", f"`{variable}`应以`)`结尾", parent=self)
                        return None
                    try:
                        return eval(variable[1:-1])
                    except:
                        messagebox.showerror("错误的变量", f"`{variable}`无法被解析", parent=self)
                        return None
                variable = variable.split(".")
                if len(variable) == 1:
                    messagebox.showerror("错误的变量", f"`{variable[0]}`没有用`.`指定属性, 或应使用`()`将其指定为字面常量", parent=self)
                    return None
                elif len(variable) == 2:
                    name, attr = variable
                    if name.startswith("<") and name.endswith(">"):
                        if len(name) == 3 and "a" <= name[1] <= "z":
                            if attr == "pressed":
                                return self._pressed[ord(name[1]) - ord("a")]
                            elif attr == "released":
                                return not self._pressed[ord(name[1]) - ord("a")]
                            else:
                                messagebox.showerror(
                                    "错误的属性", f"按键`{name}`没有属性`{attr}`\n应为`pressed`或`released`", parent=self
                                )
                                return None
                        else:
                            messagebox.showerror("错误的按键", f"不支持`{name}`", parent=self)
                            return None
                    else:
                        if name in self.widgets:
                            widget = self.widgets[name]
                            if attr in widget.data:
                                return widget.data[attr].get()
                            else:
                                messagebox.showerror("错误的属性", f"组件`{name}`没有属性{attr}", parent=self)
                                return None
                        else:
                            messagebox.showerror("错误的组件", f"组件`{name}`不存在", parent=self)
                            return None
                else:
                    messagebox.showerror("错误的变量", "变量`{}`不合法, `.`应该且只应出现一次".format(".".join(variable)), parent=self)
                    return None

            res = []
            for v in var:
                v = v.strip()
                if v:
                    res.append(getValue(v))
                    if res[-1] is None:
                        return None
            return res

        var = getVar([v for v in variables.split(";")] if variables else [])
        if var is None:
            return b""

        print(command, var)

    def registerCallback(self, name: str, command: str, variables: str, bindings: str):
        cmd = "$$".join((name, command, variables))
        for binding in bindings.split(";"):
            self.callbacks[binding].add(cmd)

    def unregisterCallback(self, name: str, command: str, variables: str, bindings: str):
        cmd = "$$".join((name, command, variables))
        for binding in bindings.split(";"):
            self.callbacks[binding].remove(cmd)

    def createCmdTable(self):
        if self.cmdTable is not None:
            self.cmdTable.focus_set()
            return
        self.cmdTable = FBWidgetCmdTable(self)
        self.cmdTable.title(f"{self.name}: 编辑指令")

    def destroyCmdTable(self):
        if self.cmdTable is not None:
            self.cmdList = self.cmdTable.toList()
            self.cmdTable.destroy()
            self.cmdTable = None

    def createWidgetFromType(self, wid_type: str):
        name = simpledialog.askstring("输入名称", "请输入名称", initialvalue=f"新组件{len(self.widgets)+1}", parent=self)
        if name:
            if name in self.widgets:
                messagebox.showerror("组件名称已存在", "组件名称已存在", parent=self)
                return None
            cur = FBWIDGET_DICT[wid_type](name)
            cur.attach(self, *self._click_pos)
            cur.dragable = self.editing
            return cur

    def createWidgetFromDict(self, cfg: dict):
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
            menu.add_command(label="结束编辑", command=lambda: self.setEditing(False))
        else:
            menu.add_command(label="编辑", command=lambda: self.setEditing(True))
        menu.add_separator()
        menu.add_command(label="切换置顶", command=self.master.toggleTopmost)
        menu.add_command(label="编辑指令", command=self.createCmdTable)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def setEditing(self, editing: bool) -> None:
        if self.editing == editing:
            return
        self.editing = editing
        self["background"] = "lightgray" if self.editing else "white"
        for widget in self.widgets.values():
            widget.dragable = editing

    def toDict(self):
        return {
            "name": self.name,
            "cmds": self.cmdList,
            "widgets": [widget.toDict() for widget in self.widgets.values()],
        }

    @classmethod
    def fromDict(cls, master, cfg):
        self = cls(master, cfg["name"])
        self.cmdList = cfg["cmds"]
        for name, command, variable, binding in self.cmdList:
            self.cmdDict[name] = (command, variable)
            self.registerCallback(name, command, variable, binding)
        for widget_cfg in cfg["widgets"]:
            widget = FBWIDGET_DICT[widget_cfg["type"]].fromDict(self, widget_cfg)
            widget.dragable = self.editing
            self.widgets[widget.name] = widget
        return self


__all__ = ["FBWidgetCanvas"]

