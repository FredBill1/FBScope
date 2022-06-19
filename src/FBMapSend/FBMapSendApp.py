import tkinter as tk
import ttkbootstrap as ttk
import os, os.path, sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from FBSocket import FBClient, FBServer
from FBFunc import as_bytes, as_float

SAVE_DIR = os.path.expanduser("~/Desktop")
SAVE_NAME_TXT = "map.txt"

HEADER = b"\x00\xff\x80\x7f"
ID = (32).to_bytes(1, "big")


class FBMapSendApp:
    def __init__(self, isServer: bool = False):
        style = ttk.Style("cosmo")
        self._root = style.master
        self._root.title("FBMapSend")
        self._root.resizable(False, False)
        self._root.protocol("WM_DELETE_WINDOW", self.shutdown)

        self._client = FBServer() if isServer else FBClient()

        self._sendButton = ttk.Button(self._root, text="发送", command=self.send)

        self._sendButton.pack(side="left", padx=5, pady=5)
        ttk.Label(self._root, text=f"路径: {os.path.join(SAVE_DIR, SAVE_NAME_TXT)}").pack(side="left", padx=5, pady=5)

    def send(self):
        if not os.path.isfile(os.path.join(SAVE_DIR, SAVE_NAME_TXT)):
            return
        with open(os.path.join(SAVE_DIR, SAVE_NAME_TXT), "r") as f:
            pointCnt = int(f.readline())
            res = (
                HEADER
                + ID
                + (pointCnt * 2).to_bytes(1, "big")
                + b"".join(as_float(float(x)) for _ in range(pointCnt) for x in f.readline().split())
            )
            self._client.send(res)

    def mainloop(self):
        self._client.start()
        self._root.mainloop()

    def shutdown(self):
        self._client.shutdown()
        self._root.destroy()


if __name__ == "__main__":
    app = FBMapSendApp()
    app.mainloop()
