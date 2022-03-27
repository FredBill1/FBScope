import tkinter as tk
from tkinter import simpledialog, messagebox
import ttkbootstrap as ttk
from typing import List, Tuple, Dict, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from FBWidgetCanvas import FBWidgetCanvas


class _FBWidgetCmdDialog(simpledialog.Dialog):
    def __init__(self, master, default: List[str], focus: int):
        self.default = default
        self.focus = focus
        super().__init__(master, title="编辑指令")
        self.unbind_all("<Escape>")

    def body(self, master):
        master.pack_configure(fill="x", expand=True)
        master.grid_columnconfigure(1, weight=1)
        WIDTH = 100

        ttk.Label(master, text="名称").grid(row=0, column=0)
        self.nameEntry = ttk.Entry(master, width=WIDTH)
        self.nameEntry.grid(row=0, column=1, sticky="ew")

        ttk.Label(master, text="指令").grid(row=1, column=0)
        self.cmdEntry = ttk.Entry(master, width=WIDTH)
        self.cmdEntry.grid(row=1, column=1, sticky="ew")

        ttk.Label(master, text="变量").grid(row=2, column=0)
        self.varEntry = ttk.Entry(master, width=WIDTH)
        self.varEntry.grid(row=2, column=1, sticky="ew")

        ttk.Label(master, text="绑定").grid(row=3, column=0)
        self.bindEntry = ttk.Entry(master, width=WIDTH)
        self.bindEntry.grid(row=3, column=1, sticky="ew")

        for i, entry in enumerate((self.nameEntry, self.cmdEntry, self.varEntry, self.bindEntry)):
            entry.insert("end", self.default[i])

        f = (self.nameEntry, self.cmdEntry, self.varEntry, self.bindEntry)[self.focus]
        f.select_range(0, "end")
        return f

    def validate(self):
        self.result = [str(entry.get()) for entry in (self.nameEntry, self.cmdEntry, self.varEntry, self.bindEntry)]
        return True

    def buttonbox(self):
        """add standard button box.

        override if you do not want the standard buttons
        """

        box = tk.Frame(self)

        w = tk.Button(box, text="OK", width=10, command=self.ok, default=tk.ACTIVE)
        w.pack(side=tk.LEFT, padx=5, pady=5)
        w = tk.Button(box, text="Cancel", width=10, command=self.cancel)
        w.pack(side=tk.LEFT, padx=5, pady=5)

        self.bind("<Return>", self.ok)
        # self.bind("<Escape>", self.cancel)

        box.pack()


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

        self.tree.heading("name", text="名称", anchor="w")
        self.tree.heading("command", text="指令", anchor="e")
        self.tree.heading("variable", text="变量", anchor="e")
        self.tree.heading("binding", text="绑定", anchor="e")
        self.tree.column("name", width=80, anchor="w")
        self.tree.column("command", width=200, anchor="e")
        self.tree.column("variable", width=200, anchor="e")
        self.tree.column("binding", width=200, anchor="e")

        self.tree.bind("<<TreeviewSelect>>", self._onSelect)
        self.tree.bind("<Double-1>", self._onDoubleClick)
        self.btn_close = ttk.Button(self.buttonFrame, text="关闭", command=master.destroyCmdTable)
        self.btn_add = ttk.Button(self.buttonFrame, text="添加", command=self._add)
        self.btn_dup = ttk.Button(self.buttonFrame, text="复制", command=self._dup)
        self.btn_del = ttk.Button(self.buttonFrame, text="删除", command=self._delete)
        self.btn_edit = ttk.Button(self.buttonFrame, text="编辑", command=self._edit)
        self.btn_up = ttk.Button(self.buttonFrame, text="上移", command=self._up)
        self.btn_down = ttk.Button(self.buttonFrame, text="下移", command=self._down)
        for btn in (
            self.btn_close,
            self.btn_add,
            self.btn_dup,
            self.btn_del,
            self.btn_edit,
            self.btn_up,
            self.btn_down,
        ):
            btn.pack(side="left", expand=True)

        self._state = "!disabled"
        self._checkSel()

        self.cmdDict = master.cmdDict

        for v in master.cmdList:
            self.tree.insert("", "end", values=v)

    def _onDoubleClick(self, event):
        if self.tree.focus() != "":
            self._edit()

    def _checkSel(self):
        cur = self.tree.focus()
        state = "disabled" if cur == "" else "!disabled"
        if self._state == state:
            return
        self._state = state
        for btn in (self.btn_dup, self.btn_del, self.btn_edit, self.btn_up, self.btn_down):
            btn["state"] = state

    def _onSelect(self, event):
        self._checkSel()

    def _add(self):
        cur = self.tree.focus()
        cur = self.tree.insert(
            "", "end" if cur == "" else int(cur[1:], 16), values=(f"新命令{len(self.cmdDict)+1}", "", "", "")
        )
        self.tree.focus(cur)
        self.tree.selection_set(cur)
        self._edit(creating=True)

    def _delete(self):
        del self.cmdDict[self.getItem(self.tree.focus())[0]]
        self.tree.delete(self.tree.focus())
        self._checkSel()

    def getItem(self, item: str):
        return [str(v) for v in self.tree.item(item)["values"]]

    def _dup(self):
        cur = self.tree.focus()
        res = self.getItem(cur)
        res[0] = f"{res[0]}-{len(self.cmdDict)+1}"
        cur = self.tree.insert("", int(cur[1:], 16), values=res)
        self.cmdDict[res[0]] = (res[1], res[2])
        self.master.registerCallback(*res)

    def _edit(self, creating=False):
        pre = res = self.getItem(self.tree.focus())
        if not creating:
            del self.cmdDict[pre[0]]
        while True:
            d = _FBWidgetCmdDialog(self.tree, res, 0 if creating else 1)
            res = d.result
            if not res:
                if creating:
                    self.tree.delete(self.tree.focus())
                else:
                    self.cmdDict[pre[0]] = (pre[1], pre[2])
                return
            if res[0] not in self.cmdDict:
                break
            messagebox.showerror("错误", "名称重复", parent=self.tree)
        self.cmdDict[res[0]] = (res[1], res[2])
        self.tree.item(self.tree.focus(), values=res)
        if not creating:
            self.master.unregisterCallback(*pre)
        self.master.registerCallback(*res)

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
        return [self.getItem(i) for i in self.tree.get_children()]


__all__ = ["FBWidgetCmdTable"]
