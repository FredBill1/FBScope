import ttkbootstrap as ttk
from os.path import join, dirname
from sys import executable
from subprocess import Popen, DETACHED_PROCESS
from math import sqrt, floor, ceil

DIR = dirname(__file__)
APPs = ["FBSerial", "FBPlot", "FBPanel", "FBRot", "FBImg", "FBRecorder", "FBPos"]

if __name__ == "__main__":
    style = ttk.Style("cosmo")
    root = style.master
    root.title("launcher")
    root.resizable(False, False)
    C = ceil(len(APPs) / floor(sqrt(len(APPs))))
    for i, app in enumerate(APPs):
        ttk.Button(
            root,
            text=app,
            command=lambda app=app: Popen([executable, join(DIR, app, "main.py")], creationflags=DETACHED_PROCESS),
        ).grid(row=i // C, column=i % C, padx=5, pady=5, sticky="nsew")
    root.mainloop()

