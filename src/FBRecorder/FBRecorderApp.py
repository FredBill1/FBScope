import tkinter as tk
import ttkbootstrap as ttk
from tkinter import filedialog, messagebox
from typing import List
from os.path import join, dirname, isfile
import os, sys
import json
import threading
from datetime import datetime

sys.path.append(join(dirname(__file__), ".."))

from FBCSV import FBCSVWriter
from FBSocket import FBServer, FBClient
from FBRecv import FBFloatMultiRecv

SAVE_PATH = os.path.expanduser("~/Desktop/1.csv")
CFG_DIR = os.path.expanduser("~/.FBScope")
CFG_PATH = os.path.join(CFG_DIR, "FBRecorder.json")


class FBRecorderApp:
    def __init__(self, isServer: bool = False):
        style = ttk.Style("cosmo")
        self._root = style.master
        self._root.title("FBRecorder")
        self._root.resizable(False, False)
        self._root.protocol("WM_DELETE_WINDOW", self.shutdown)

        self._recv = FBFloatMultiRecv()
        self._recv.registerRecvAllCallback(self.updateData)
        self._client = FBServer() if isServer else FBClient()
        self._client.registerRecvCallback(self._recv.input)

        self._csvWriter: FBCSVWriter = None
        self._cvsWriterLock = threading.Lock()

        self.cnt = 0
        self._cntLock = threading.Lock()
        self._cntVar = tk.StringVar(value="0")

        cfgFrame = ttk.Frame(self._root)
        cfgFrame.pack(padx=5, pady=5)
        self.cfg_path = tk.StringVar()
        self._cfgPathEntry = ttk.Entry(cfgFrame, textvariable=self.cfg_path, state="readonly", width=30)
        self._cfgPathButton = ttk.Button(cfgFrame, text="选择", command=self._selectCfgPath)

        ttk.Label(cfgFrame, text="配置文件").pack(side="left")
        self._cfgPathEntry.pack(side="left")
        self._cfgPathButton.pack(side="left")

        saveFrame = ttk.Frame(self._root)
        saveFrame.pack(padx=5, pady=5)
        self.save_path = tk.StringVar()
        self._savePathEntry = ttk.Entry(saveFrame, textvariable=self.save_path, state="readonly", width=30)
        self._savePathButton = ttk.Button(saveFrame, text="选择", command=self._selectSavePath)

        ttk.Label(saveFrame, text="保存文件").pack(side="left")
        self._savePathEntry.pack(side="left")
        self._savePathButton.pack(side="left")

        opFrame = ttk.Frame(self._root)
        opFrame.pack(padx=5, pady=5, fill="x", expand=True)
        self._appendsButton = ttk.Checkbutton(opFrame, text="追加", bootstyle=("info", "outline", "toolbutton"),)
        self._recordButton = ttk.Checkbutton(
            opFrame, text="录制", command=self._toggleRecord, bootstyle=("warning", "outline", "toolbutton")
        )
        self._pauseButton = ttk.Checkbutton(opFrame, text="暂停", bootstyle=("success", "outline", "toolbutton"))

        self._appendsButton.pack(side="left")
        self._recordButton.pack(side="left", padx=5)
        self._pauseButton.pack(side="left")
        ttk.Label(opFrame, text="已接收:").pack(side="left")
        ttk.Label(opFrame, textvariable=self._cntVar).pack(side="left")

    def loadConfig(self):
        os.makedirs(CFG_DIR, exist_ok=True)
        cfg = {}
        if os.path.exists(CFG_PATH):
            with open(CFG_PATH, "r") as f:
                cfg = json.load(f)
        self.cfg_path.set(cfg.get("cfg_path", ""))
        self.save_path.set(cfg.get("save_path", SAVE_PATH))
        if cfg.get("appends", False):
            self._appendsButton.invoke()

    def saveConfig(self):
        cfg = {
            "cfg_path": self.cfg_path.get(),
            "save_path": self.save_path.get(),
            "appends": self._appendsButton.instate(["selected"]),
        }
        with open(CFG_PATH, "w") as f:
            json.dump(cfg, f)

    def _increaseCnt(self):
        with self._cntLock:
            self.cnt += 1

    def _updateCnt(self):
        with self._cntLock:
            cnt = self.cnt
        self._cntVar.set(str(cnt))
        self._root.after(100, self._updateCnt)

    def mainloop(self):
        self.loadConfig()
        self._client.start()
        self._recv.start()
        self._updateCnt()
        self._root.mainloop()

    def shutdown(self):
        self._recv.shutdown()
        self._client.shutdown()
        self._stopWriter()
        self.saveConfig()
        self._root.destroy()

    def updateData(self, id: int, data: List[float]):
        if self._pauseButton.instate(["selected"]):
            return
        with self._cvsWriterLock:
            writer = self._csvWriter
        if writer is None:
            return
        self._increaseCnt()
        writer.write(map(str, (datetime.timestamp(datetime.now()), id, *data)))

    def _toggleRecord(self, *_):
        if self._recordButton.instate(["selected"]):
            self._recordButton.config(text="停止")
            self._cfgPathButton.config(state="disabled")
            self._savePathButton.config(state="disabled")
            self._appendsButton.config(state="disabled")
            self._startWriter()
        else:
            self._recordButton.config(text="录制")
            self._cfgPathButton.config(state="!disabled")
            self._savePathButton.config(state="!disabled")
            self._appendsButton.config(state="!disabled")
            self._stopWriter()

    def _startWriter(self):
        self._stopWriter()
        self._recv.resetConfig()
        cfg_path = self.cfg_path.get()
        if not isfile(cfg_path):
            messagebox.showerror("错误", "配置文件不存在", parent=self._root)
            self._recordButton.invoke()
            return
        self._recv.loadCfgFromCSV(cfg_path)
        save_path = self.save_path.get()
        with self._cvsWriterLock:
            self._csvWriter = FBCSVWriter(save_path, appends=self._appendsButton.instate(["selected"]))

    def _stopWriter(self):
        with self._cvsWriterLock:
            writer = self._csvWriter
            self._csvWriter = None
        if writer is not None:
            writer.close()

    def _selectCfgPath(self, *_):
        s = filedialog.askopenfilename(
            master=self._root,
            initialfile=self.cfg_path.get(),
            filetypes=[("csv file", "*.csv"), ("all files", "*.*")],
            defaultextension="csv file",
            title="选择配置文件",
        )
        if s and isfile(s):
            self.cfg_path.set(s)

    def _selectSavePath(self, *_):
        s = filedialog.asksaveasfilename(
            master=self._root,
            initialfile=self.save_path.get(),
            filetypes=[("csv file", "*.csv"), ("all files", "*.*")],
            defaultextension="csv file",
            title="选择保存路径",
            confirmoverwrite=False,
        )
        if s:
            os.makedirs(dirname(s), exist_ok=True)
            self.save_path.set(s)


if __name__ == "__main__":
    app = FBRecorderApp(isServer=True)
    app.mainloop()
