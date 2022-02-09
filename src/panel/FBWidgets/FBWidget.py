from typing import List, Dict, Set, Callable, TYPE_CHECKING
import tkinter as tk
from DND import DNDBase
from tkinter import simpledialog, messagebox

if TYPE_CHECKING:
    from FBWidgetCanvas import FBWidgetCanvas


class FBWidget(DNDBase):
    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self.data: Dict[str, tk.StringVar] = {}
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
        name = simpledialog.askstring("输入名称", "输入名称", initialvalue=self.name, parent=self.frame)
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
        self.applyConfig()

    def applyConfig(self):
        ...

    def _rightClick(self, event):
        if not self._dragable:
            return
        menu = tk.Menu(self.frame, tearoff=0)
        if self.config:
            configMenu = tk.Menu(menu, tearoff=0)
            for key, value in self.config.items():
                configMenu.add_command(label=f"{key}: {value}", command=lambda key=key: self.configure(key))
            menu.add_cascade(label="配置", menu=configMenu)
            menu.add_separator()
        menu.add_command(label="重命名", command=self.rename)
        menu.add_command(label="删除", command=self.detach)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def configure(self, key: str):
        res = simpledialog.askstring(f"输入{key}", f"输入{key}", initialvalue=self.config[key], parent=self.frame)
        if res:
            if res != self.config[key]:
                pre = self.config[key]
                self.config[key] = res
                try:
                    self.applyConfig()
                except:
                    self.config[key] = pre
                    self.applyConfig()
                    messagebox.showerror("输入无效", "输入无效", parent=self.frame)

    def toDict(self) -> dict:
        return {
            "name": self.name,
            "type": type(self).__name__,
            "pos": self.pos(),
            "data": {k: v.get() for k, v in self.data.items()},
            "config": self.config,
        }

    @classmethod
    def fromDict(cls, cfg: dict, canvas: "FBWidgetCanvas") -> "FBWidget":
        res = cls(cfg["name"])
        res.data = {k: tk.StringVar(value=v) for k, v in cfg["data"].items()}
        res.config = cfg["config"]
        res.attach(canvas, *cfg["pos"])
        return res

