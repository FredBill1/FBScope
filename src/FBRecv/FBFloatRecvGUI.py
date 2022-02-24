import sys, os, os.path
import ttkbootstrap as ttk
import json

sys.path.append(os.path.dirname(__file__))
from FBFloatRecv import FBFloatRecv
from utils import ValEntry


CFG_DIR = os.path.expanduser("~/.FBScope")
CFG_PATH = os.path.join(CFG_DIR, "FBFloatRecvGUI.json")


class FBFloatRecvGUI(ttk.Frame):
    def __init__(self, master=None, is_vertical=True, queue_size: int = 10, **kw):
        super().__init__(master, **kw)
        self._recv = FBFloatRecv(queue_size=queue_size)
        self.input = self._recv.input
        self.registerRecvCallback = self._recv.registerRecvCallback
        self.start = self._recv.start

        idLabel = ttk.Label(self, text="ID")
        self._idCbo = ttk.Combobox(self, width=4, state="readonly", values=["无"] + list(range(256)))
        self._idCbo.current(0)
        self._idCbo.bind("<<ComboboxSelected>>", self._applyID)

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
            idLabel.grid(row=0, column=0, sticky="w")
            self._idCbo.grid(row=0, column=1, sticky="w")
            cntLabel.grid(row=1, column=0, sticky="w")
            self._cntEntry.grid(row=1, column=1, sticky="we")
            bitsLabel.grid(row=2, column=0, sticky="w")
            self._bitsCbo.grid(row=2, column=1, sticky="we")
            checkLabel.grid(row=3, column=0, sticky="w")
            self._checkCbo.grid(row=3, column=1, sticky="we")
            if extra is not None:
                extra.grid(row=4, column=0, columnspan=2, sticky="we")
            applyButton.grid(row=4 + (extra is not None), column=0, columnspan=2, sticky="we")
        else:
            idLabel.pack(side="left")
            self._idCbo.pack(side="left", padx=2)
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

    def getID(self):
        return self._idCbo.current() - 1

    def getCnt(self):
        return int(self._cntEntry.get())

    def _applyConfig(self):
        id = self.getID()
        self.cfg["id"] = str(id)
        cfg = self.cfg["cfg"][str(id)]
        cnt = cfg["cnt"] = self.getCnt()
        bits = cfg["bits"] = int(self._bitsCbo.get())
        check = cfg["check"] = self._checkCbo.get()
        self._recv.setConfig(id=id, cnt=cnt, bits=bits, checksum=check == "sum")

    @staticmethod
    def _getDefualtCfg():
        return {"cnt": 1, "bits": 4, "check": "sum"}

    def _applyID(self, *_):
        cfg = self.cfg["cfg"].setdefault(str(self.getID()), self._getDefualtCfg())
        self._cntEntry.set(str(cfg["cnt"]))
        self._bitsCbo.current(0 if cfg["bits"] == 4 else 1)
        self._checkCbo.current(0 if cfg["check"] == "sum" else 1)

    def loadConfig(self):
        os.makedirs(CFG_DIR, exist_ok=True)
        self.cfg = {}
        if os.path.exists(CFG_PATH):
            with open(CFG_PATH, "r") as f:
                self.cfg = json.load(f)
        id = self.cfg.setdefault("id", "-1")
        self._idCbo.current(int(id) + 1)
        self.cfg.setdefault("cfg", {})
        self._applyID()
        self._applyConfig()

    def saveConfig(self):
        res = {"id": self.cfg["id"], "cfg": {}}
        defaultCfg = self._getDefualtCfg()
        for id, cfg in self.cfg["cfg"].items():
            if cfg != defaultCfg:
                res["cfg"][id] = cfg

        with open(CFG_PATH, "w") as f:
            json.dump(res, f)

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
