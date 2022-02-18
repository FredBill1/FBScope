import sys, os, os.path
import ttkbootstrap as ttk
import json

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from FBFloatRecv import FBFloatRecv
from utils import ValEntry


CFG_DIR = os.path.expanduser("~/.FBScope")
CFG_PATH = os.path.join(CFG_DIR, "FBFloatRecvGUI.json")


class FBFloatRecvGUI(ttk.Frame):
    def __init__(self, master=None, is_vertical=True, **kw):
        super().__init__(master, **kw)
        self._recv = FBFloatRecv()
        self.input = self._recv.input
        self.registerRecvCallback = self._recv.registerRecvCallback
        self.start = self._recv.start

        cntLabel = ttk.Label(self, text="个数")
        self._cntEntry = ValEntry(lambda s: s.isdigit() and int(s) > 0, self, width=5)

        bitsLabel = ttk.Label(self, text="位数")
        self._bitsCbo = ttk.Combobox(self, width=4, state="readonly", values=[4, 8])
        self._bitsCbo.current(0)

        checkLabel = ttk.Label(self, text="校验")
        self._checkCbo = ttk.Combobox(self, width=4, state="readonly", values=["sum", "none"])
        self._checkCbo.current(0)

        extra = self.extraBody(self)

        self._cbs: callable = []
        applyButton = ttk.Button(self, text="应用", command=self._clickCB)

        if is_vertical:
            cntLabel.grid(row=0, column=0, sticky="w")
            self._cntEntry.grid(row=0, column=1, sticky="we")
            bitsLabel.grid(row=1, column=0, sticky="w")
            self._bitsCbo.grid(row=1, column=1, sticky="we")
            checkLabel.grid(row=2, column=0, sticky="w")
            self._checkCbo.grid(row=2, column=1, sticky="we")
            if extra is not None:
                extra.grid(row=3, column=0, columnspan=2, sticky="we")
            applyButton.grid(row=3 + (extra is not None), column=0, columnspan=2, sticky="we")
        else:
            cntLabel.pack(side="left")
            self._cntEntry.pack(side="left", padx=2)
            bitsLabel.pack(side="left")
            self._bitsCbo.pack(side="left", padx=2)
            checkLabel.pack(side="left")
            self._checkCbo.pack(side="left", padx=2)
            if extra is not None:
                extra.pack(side="left")
            applyButton.pack(side="left", padx=2)

        self.loadConfig()

    def extraBody(self, master: ttk.Frame) -> ttk.Frame:
        return None

    def registerClickCallback(self, func: callable):
        self._cbs.append(func)

    def _clickCB(self):
        self._applyConfig()
        for cb in self._cbs:
            cb()

    def getCnt(self):
        return int(self._cntEntry.get())

    def _applyConfig(self):
        cnt = self.getCnt()
        bits = int(self._bitsCbo.get())
        check = True if self._checkCbo.get() == "sum" else False
        self._recv.setConfig(cnt=cnt, bits=bits, checksum=check)

    def loadConfig(self):
        os.makedirs(CFG_DIR, exist_ok=True)
        cfg = {}
        if os.path.exists(CFG_PATH):
            with open(CFG_PATH, "r") as f:
                cfg = json.load(f)
        self._cntEntry.set(cfg.get("cnt", "1"))
        self._bitsCbo.current(0 if cfg.get("bits", 4) == "4" else 1)
        self._checkCbo.current(0 if cfg.get("check", "sum") == "sum" else 1)
        self._applyConfig()

    def toDict(self):
        return {"cnt": self._cntEntry.get(), "bits": self._bitsCbo.get(), "check": self._checkCbo.get()}

    def saveConfig(self):
        with open(CFG_PATH, "w") as f:
            json.dump(self.toDict(), f)

    def shutdown(self):
        self.saveConfig()
        self._recv.shutdown()


__all__ = ["FBFloatRecvGUI"]

if __name__ == "__main__":
    from ttkbootstrap import Style

    style = Style("cosmo")
    root = style.master

    recv = FBFloatRecvGUI(root)
    recv.pack()

    root.protocol("WM_DELETE_WINDOW", lambda: (recv.saveConfig(), root.destroy()))

    root.mainloop()
