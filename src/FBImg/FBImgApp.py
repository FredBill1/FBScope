import ttkbootstrap as ttk
import os, os.path, sys
import json
from tkinter import filedialog
import tkinter as tk
import numpy as np
import cv2 as cv
from PIL import ImageTk, Image
import threading
import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from FBSocket import FBClient, FBServer
from utils import ValEntry
from FBRecv import FBRawRecv

SAVE_DIR = os.path.expanduser("~/Desktop")
SAVE_EXT = ".png"
CFG_DIR = os.path.expanduser("~/.FBScope")
CFG_PATH = os.path.join(CFG_DIR, "FBImg.json")


class FBImgApp:
    def __init__(self, isServer: bool = False):
        style = ttk.Style("cosmo")
        self._root = style.master
        self._root.title("FBImg")
        self._root.rowconfigure(0, weight=1)
        self._root.columnconfigure(0, weight=1)
        self._root.protocol("WM_DELETE_WINDOW", self.shutdown)

        self._imgCanvas = ttk.Canvas(self._root)
        self._imgCanvas.config(bg="light gray")
        self._imgCanvas.grid(row=0, column=0, sticky="nsew")
        self._imgCanvas_shape = (0, 0)

        opFrame = ttk.Frame(self._root)
        opFrame.grid(row=1, column=0, sticky="we")
        opFrame.columnconfigure(0, weight=1)

        val = lambda s: ValEntry.type_validator(int)(s) and int(s) > 0
        imgFrame = ttk.Frame(opFrame)
        imgFrame.grid(row=0, column=0, sticky="we")
        ttk.Label(imgFrame, text="宽度").pack(side="left", pady=5)
        self.wEntry = ValEntry(val, imgFrame, width=5)
        self.wEntry.pack(side="left", pady=5)
        ttk.Label(imgFrame, text="高度").pack(side="left", pady=5)
        self.hEntry = ValEntry(val, imgFrame, width=5)
        self.hEntry.pack(side="left", pady=5)
        ttk.Button(imgFrame, text="应用", command=self._applySize).pack(side="left", padx=2, pady=5)

        self._pauseButton = ttk.Checkbutton(imgFrame, text="暂停", bootstyle=("success", "outline", "toolbutton"))
        self._pauseButton.pack(side="left", padx=5, pady=5)

        ttk.Label(imgFrame, text="保存路径").pack(side="left", pady=5)
        self._dirEntry = ttk.Entry(imgFrame, width=30)
        self._dirEntry.pack(side="left", pady=5)

        ttk.Button(imgFrame, text="选择", command=self._selectDir).pack(side="left", pady=5)

        self._saveButton = ttk.Button(imgFrame, text="保存", bootstyle=("success"), command=self.saveImg)
        self._saveButton.pack(side="left", padx=5, pady=5)
        self._recordButton = ttk.Checkbutton(
            imgFrame, text="录制", command=self._toggleRecord, bootstyle=("warning", "outline", "toolbutton")
        )
        self._recordButton.pack(side="left", pady=5)
        self._cntLabel = ttk.Label(imgFrame)
        self._cntLabel.pack(side="left", pady=5)

        self._client = FBServer() if isServer else FBClient()
        self._recv = FBRawRecv()

        self._client.registerRecvCallback(self._recv.input)
        self._recv.registerRecvCallback(self.updateData)

        self._imgLock = threading.Lock()
        self._dirLock = threading.Lock()
        self.loadConfig()

    def _toggleRecord(self, *_):
        if self._recordButton.instate(["selected"]):
            self._saveButton.config(state="disabled")
            self._recordButton.config(text="停止")
        else:
            self._saveButton.config(state="!disabled")
            self._recordButton.config(text="录制")

    def _updateDir(self):
        os.makedirs(self.save_dir, exist_ok=True)
        self._dirEntry.config(state="normal")
        self._dirEntry.delete(0, tk.END)
        self._dirEntry.insert(0, self.save_dir)
        self._dirEntry.config(state="readonly")

    def _selectDir(self, *_):
        with self._dirLock:
            cur = self.save_dir
        s = filedialog.askdirectory(master=self._root, initialdir=cur, title="选择保存路径", mustexist=False)
        if not s:
            return
        with self._dirLock:
            self.save_dir = s
        self._updateDir()

    def saveImg(self, *_):
        def save():
            with self._imgLock:
                img = self.img
            with self._dirLock:
                Dir = self.save_dir
            name = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f") + SAVE_EXT
            cv.imwrite(os.path.join(Dir, name), img)

        threading.Thread(target=save).start()

    def updateData(self, data: bytes) -> None:
        if self._pauseButton.instate(["selected"]):
            return
        with self._imgLock:
            w, h = self.w, self.h
        img = np.frombuffer(data, dtype=np.uint8).reshape((h, w))
        with self._imgLock:
            if w != self.w or h != self.h:
                return
            self.img = img
            self._updateFlag = True
        if self._recordButton.instate(["selected"]):
            self.saveImg()

    def _applySize(self):
        with self._imgLock:
            self.w, self.h = int(self.wEntry.get()), int(self.hEntry.get())
            self.img = np.zeros((self.h, self.w), dtype=np.uint8)
            self._updateFlag = True
        self._recv.setConfig(cnt=self.w * self.h)

    def loadConfig(self):
        os.makedirs(CFG_DIR, exist_ok=True)
        cfg = {}
        if os.path.exists(CFG_PATH):
            with open(CFG_PATH, "r") as f:
                cfg = json.load(f)
        self._root.geometry(cfg.get("geometry", "876x600+30+30"))
        self.w = cfg.get("w", 752)
        self.h = cfg.get("h", 480)
        self.wEntry.set(str(self.w))
        self.hEntry.set(str(self.h))
        self.save_dir = cfg.get("save_dir", SAVE_DIR)
        self._updateDir()
        self._applySize()

    def saveConfig(self):
        cfg = {"geometry": self._root.geometry(), "w": self.w, "h": self.h, "save_dir": self.save_dir}
        with open(CFG_PATH, "w") as f:
            json.dump(cfg, f)

    def create_image(self):
        canvas_w, canvas_h = self._imgCanvas.winfo_width(), self._imgCanvas.winfo_height()
        with self._imgLock:
            if (canvas_w, canvas_h) == self._imgCanvas_shape and not self._updateFlag:
                return
            img = self.img
            self._updateFlag = False
        self._imgCanvas_shape = (canvas_w, canvas_h)

        img_w, img_h = img.shape[1], img.shape[0]
        canvas_k, img_k = canvas_w / canvas_h, img_w / img_h
        w, h = (canvas_w, round(canvas_w / img_k)) if canvas_k < img_k else (round(canvas_h * img_k), canvas_h)
        resized_img = cv.resize(img, (max(1, w), max(1, h)), interpolation=cv.INTER_NEAREST)
        cvt_img = resized_img
        self._imgTK = ImageTk.PhotoImage(master=self._imgCanvas, image=Image.fromarray(cvt_img))
        self._imgCanvas.create_image(canvas_w >> 1, canvas_h >> 1, image=self._imgTK)

    def _create_image_task(self):
        if self._running:
            self.create_image()
        if self._running:
            self._imgCanvas.after(50, self._create_image_task)

    def mainloop(self):
        self._running = True
        self._updateFlag = True
        self._create_image_task()
        self._client.start()
        self._recv.start()
        self._root.mainloop()

    def shutdown(self):
        self._running = False
        self._recv.shutdown()
        self._client.shutdown()
        self.saveConfig()
        self._root.destroy()


if __name__ == "__main__":
    app = FBImgApp()
    app.mainloop()
