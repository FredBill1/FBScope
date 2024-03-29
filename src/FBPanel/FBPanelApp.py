from FBWidgetTabs import FBWidgetTabs
from ttkbootstrap import Style
import os, os.path, sys
import json
import tkinter as tk

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from FBSocket import FBClient, FBServer

CFG_DIR = os.path.expanduser("~/.FBScope")
CFG_PATH = os.path.join(CFG_DIR, "FBPanel.json")


class FBPanelApp:
    def __init__(self, cfg: dict = None, isServer: bool = False):
        os.makedirs(CFG_DIR, exist_ok=True)
        if cfg is None and os.path.exists(CFG_PATH):
            with open(CFG_PATH, "r") as f:
                cfg = json.load(f)
        if cfg is None:
            cfg = {"canvases": []}

        self.uartClient = FBServer() if isServer else FBClient()
        self.uartClient.start()

        style = Style("cosmo")
        self.root: tk.Tk = style.master
        self.root.title("FBPanel")
        self.tabs = FBWidgetTabs.fromDict(self.uartClient, self.root, cfg)
        self.tabs.pack(fill="both", expand=True)

        self.root.geometry(cfg.get("geometry", "400x300+30+30"))
        self.root.protocol("WM_DELETE_WINDOW", self.onClose)

        self.mainloop = self.root.mainloop

    def toDict(self):
        return {"geometry": self.root.winfo_geometry(), "canvases": self.tabs.toList()}

    def onClose(self):
        self.uartClient.shutdown()

        for canvas in self.tabs.canvases:
            canvas.destroyCmdTable()
        with open(CFG_PATH, "w") as f:
            json.dump(self.toDict(), f, indent=4)
        self.root.destroy()


__all__ = ["FBPanelApp"]
