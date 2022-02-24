import ttkbootstrap as ttk
from os.path import join, dirname
from sys import executable
from subprocess import Popen, DETACHED_PROCESS

DIR = dirname(__file__)
APPs = ["FBSerial", "FBPlot", "FBPanel", "FBRot", "FBImg"]

if __name__ == "__main__":
    style = ttk.Style("cosmo")
    root = style.master
    root.title("launcher")
    root.resizable(False, False)
    for app in APPs:
        ttk.Button(
            root,
            text=app,
            command=lambda app=app: Popen([executable, join(DIR, app, "main.py")], creationflags=DETACHED_PROCESS),
        ).pack(side="left", padx=5, pady=5, fill="both", expand=True)
    root.mainloop()

