import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from typing import List, Tuple, Dict, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from FBWidgetCanvas import FBWidgetCanvas


class _FBWidgetCmdDialog(simpledialog.Dialog):
    def __init__(self, master, default: List[str], focus: int):
        self.default = default
        self.focus = focus
        super().__init__(master, title="编辑指令")

    def body(self, master):
        ttk.Label(master, text="名称").grid(row=0, column=0)
        self.nameEntry = ttk.Entry(master)
        self.nameEntry.grid(row=0, column=1)

        ttk.Label(master, text="指令").grid(row=1, column=0)
        self.cmdEntry = ttk.Entry(master)
        self.cmdEntry.grid(row=1, column=1)

        ttk.Label(master, text="变量").grid(row=2, column=0)
        self.varEntry = ttk.Entry(master)
        self.varEntry.grid(row=2, column=1)

        ttk.Label(master, text="绑定").grid(row=3, column=0)
        self.bindEntry = ttk.Entry(master)
        self.bindEntry.grid(row=3, column=1)

        for i, entry in enumerate((self.nameEntry, self.cmdEntry, self.varEntry, self.bindEntry)):
            entry.insert("end", self.default[i])

        f = (self.nameEntry, self.cmdEntry, self.varEntry, self.bindEntry)[self.focus]
        f.select_range(0, "end")
        return f

    def validate(self):
        self.result = [entry.get() for entry in (self.nameEntry, self.cmdEntry, self.varEntry, self.bindEntry)]
        return True


class FBWidgetCmdTable(tk.Toplevel):
    def __init__(self, master: "FBWidgetCanvas"):
        super().__init__(master)
        self.protocol("WM_DELETE_WINDOW", master.destroyCmdTable)

        self.tableFrame = ttk.Frame(self)
        self.tableFrame.pack(fill="both", expand=True)

        self.buttonFrame = ttk.Frame(self)
        self.buttonFrame.pack(fill="x", ipadx=5, ipady=5)

        self.tree = ttk.Treeview(self.tableFrame, columns=["name", "command", "variable", "binding"], show="headings")
        self.scrollbar = ttk.Scrollbar(self.tableFrame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="right", fill="both", expand=True)

        self.tree.heading("name", text="名称", anchor="c")
        self.tree.heading("command", text="指令", anchor="c")
        self.tree.heading("variable", text="变量", anchor="c")
        self.tree.heading("binding", text="绑定", anchor="c")

        self.tree.bind("<<TreeviewSelect>>", self._onSelect)
        self.btn_add = ttk.Button(self.buttonFrame, text="添加", command=self._add)
        self.btn_del = ttk.Button(self.buttonFrame, text="删除", command=self._delete)
        self.btn_edit = ttk.Button(self.buttonFrame, text="编辑", command=self._edit)
        self.btn_up = ttk.Button(self.buttonFrame, text="上移", command=self._up)
        self.btn_down = ttk.Button(self.buttonFrame, text="下移", command=self._down)
        for btn in (self.btn_add, self.btn_del, self.btn_edit, self.btn_up, self.btn_down):
            btn.pack(side="left", expand=True)

        self._state = "!disabled"
        self._checkSel()

        self.cmdDict = master.cmdDict

        for v in master.cmdList:
            self.tree.insert("", "end", values=v)

    def _checkSel(self):
        cur = self.tree.focus()
        state = "disabled" if cur == "" else "!disabled"
        if self._state == state:
            return
        self._state = state
        for btn in (self.btn_del, self.btn_edit, self.btn_up, self.btn_down):
            btn["state"] = state

    def _onSelect(self, event):
        self._checkSel()

    def _add(self):
        cur = self.tree.focus()
        cur = self.tree.insert(
            "", "end" if cur == "" else int(cur[1:]), values=(f"新命令{len(self.cmdDict)+1}", "", "", "")
        )
        self.tree.focus(cur)
        self.tree.selection_set(cur)
        self._edit(creating=True)

    def _delete(self):
        self.tree.delete(self.tree.focus())
        self._checkSel()

    def _edit(self, creating=False):
        pre = res = self.tree.item(self.tree.focus())["values"]
        if not creating:
            del self.cmdDict[pre[0]]
        while True:
            d = _FBWidgetCmdDialog(self.tree, res, 0 if creating else 1)
            res = d.result
            if not res:
                if creating:
                    self.tree.delete(self.tree.focus())
                else:
                    self.cmdDict[pre[0]] = pre[1]
                return
            if res[0] not in self.cmdDict:
                break
            messagebox.showerror("错误", "名称重复", parent=self.tree)
        self.cmdDict[res[0]] = res[1]
        self.tree.item(self.tree.focus(), values=res)

    def _up(self):
        cur = self.tree.focus()
        idx = self.tree.index(cur)
        if idx > 0:
            self.tree.move(cur, "", idx - 1)

    def _down(self):
        cur = self.tree.focus()
        idx = self.tree.index(cur)
        if idx < len(self.cmdDict) - 1:
            self.tree.move(cur, "", idx + 1)

    def toList(self):
        return [self.tree.item(i)["values"] for i in self.tree.get_children()]


__all__ = ["FBWidgetCmdTable"]
