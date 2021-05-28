from .Main import Main


class PID:
    def __init__(self, main: Main) -> None:
        from tkinter import Toplevel

        self.main = main
        self.root = Toplevel(self.main.root)
        self.setProperty()

    def setProperty(self) -> None:
        from tkinter import StringVar
        from tkinter.ttk import LabelFrame, Button, Label, Entry

        names = ("L1", "L2", "R1", "R2")
        texts = ("KP:", "KI:", "KD:")

        self.frames = [LabelFrame(self.root, text=names[i]) for i in range(len(names))]
        self.texts = [[Label(self.frames[i], text=texts[j]) for j in range(len(texts))] for i in range(len(names))]
        self.strings = [[StringVar() for j in range(len(texts))] for i in range(len(names))]
        self.entries = [[Entry(self.frames[i], textvariable=self.strings[i][j], validate="focusout", validatecommand=lambda i=i, j=j: self.entryCallback(i, j), width=10,) for j in range(len(texts))] for i in range(len(names))]
        self.uploadButtons = [Button(self.frames[i], text="上传", state="disabled", command=lambda i=i: self.upload(i)) for i in range(len(names))]

        self.root.title("FBScope - PID")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)

        for i in range(len(names)):
            self.frames[i].pack(padx=3)
            for j in range(len(texts)):
                self.texts[i][j].pack(side="left")
                self.entries[i][j].pack(side="left", padx=3, pady=1)
            self.uploadButtons[i].pack(padx=3)

        self.getConfig()
        self.setConfig()

        if "PID" in self.main.Config["WINDOWPOSITION"]:
            self.root.geometry(self.main.Config["WINDOWPOSITION"]["PID"])

    def getConfig(self):
        keys = ("L1", "L2", "R1", "R2")
        self.Config = [self.main.Config["PID"][key] for key in keys]
        self.HEAD = self.main.Config["PID"]["HEAD"]

    def setConfig(self):
        for i in range(len(self.frames)):
            for j in range(3):
                self.strings[i][j].set(str(self.Config[i][j]))

    def entryCallback(self, i, j):
        try:
            self.Config[i][j] = float(self.strings[i][j].get())
            return True
        except:
            self.strings[i][j].set(str(self.Config[i][j]))
            return False

    def upload(self, i):
        from numpy import array

        self.main.write(self.HEAD + bytes([i]) + array(self.Config[i]).astype("float32").tobytes())
        self.root.bell()

    def setActivate(self, activate: bool):
        state = ("disabled", "normal")
        for button in self.uploadButtons:
            button["state"] = state[activate]

