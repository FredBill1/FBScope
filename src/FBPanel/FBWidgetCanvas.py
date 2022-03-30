from typing import List, Dict, Set, Callable, TYPE_CHECKING, Tuple, Optional
import tkinter as tk
import ttkbootstrap as ttk
from DND import *
from collections import defaultdict
from tkinter import simpledialog, messagebox
from FBWidgets import FBWidget, FBWIDGET_DICT
from FBWidgetCmdTable import FBWidgetCmdTable
from FBinterpreter import interpretCmd

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
        self._spacePressed = False

    def _keyPress(self, event):
        if event.char == " ":
            if not self._spacePressed:
                self._spacePressed = True
                self._callback("<space>", "press")
                self._callback("<space>", "period")
                self._callback("<space>", "both")
        elif "a" <= event.char <= "z":
            cur = ord(event.char) - ord("a")
            if not self._pressed[cur]:
                self._pressed[cur] = True
                self._callback(f"<{event.char}>", "press")
                self._callback(f"<{event.char}>", "period")
                self._callback(f"<{event.char}>", "both")

    def _keyRelease(self, event):
        if event.char == " ":
            self._spacePressed = False
            self._callback("<space>", "release")
            self._callback("<space>", "both")
        elif "a" <= event.char <= "z":
            self._pressed[ord(event.char) - ord("a")] = False
            self._callback(f"<{event.char}>", "release")
            self._callback(f"<{event.char}>", "both")

    def _checkPeriod(self, name: str) -> bool:
        if (name.startswith("<") and name.endswith(">") and len(name) == 3) or name == "<space>":
            key = name[1:-1]
            if key == "space":
                return self._spacePressed
            else:
                return self._pressed[ord(key) - ord("a")]
        else:
            return self.widgets[name].checkPeriod()

    def _callback(self, name: str, event: str) -> None:
        cur = f"{name}.{event}"
        if cur in self.callbacks:
            for cmd in self.callbacks[cur]:
                cmd, period = cmd.split("@@")
                period = int(period)
                if period > 0 and not self._checkPeriod(name):
                    continue

                res = interpretCmd(self, cmd)
                if res is not None:
                    self.master.uartClient.send(res)
                    print("发送:", (" ".join("%02x" % b for b in res)).upper())
                    if period > 0:
                        self.after(period, lambda name=name, event=event: self._callback(name, event))

    @staticmethod
    def getCmd(name: str, command: str, variables: str, binding: str) -> Tuple[str, str]:
        PERIOD_STR = ".period("
        period = 0
        if binding.endswith(")"):
            i = binding.find(PERIOD_STR)
            if i != -1:
                period_tmp = binding[i + len(PERIOD_STR) : -1]
                if period_tmp and period_tmp.isdigit():
                    period = int(period_tmp)
                    binding = binding[: i + len(PERIOD_STR) - 1]
        return binding, "$$".join((name, command, variables)) + f"@@{period}"

    def registerCallback(self, name: str, command: str, variables: str, bindings: str):
        for binding in bindings.split(";"):
            binding, cmd = self.getCmd(name, command, variables, binding)
            self.callbacks[binding].add(cmd)

    def unregisterCallback(self, name: str, command: str, variables: str, bindings: str):
        for binding in bindings.split(";"):
            binding, cmd = self.getCmd(name, command, variables, binding)
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
        menu.add_cascade(label="新建组件", menu=self.create_menu)
        if self.editing:
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

