from .Main import Main


class Patrol:
    def __init__(self, main: Main) -> None:
        from tkinter import Toplevel

        self.main = main
        self.root = Toplevel(self.main.root)
        self.enabled = False
        self.getConfig()
        self.setProperty()

    def getConfig(self):
        self.SETPARAMS = self.main.Config["PATROL"]["SETPARAMS"]
        self.PARAMS = self.main.Config["PATROL"]["PARAMS"]
        self.NAMES = self.main.Config["PATROL"]["NAMES"]
        if len(self.NAMES) > len(self.PARAMS):
            self.PARAMS += [0.0] * (len(self.NAMES) - len(self.PARAMS))

    def setProperty(self):
        from tkinter import StringVar
        from tkinter.ttk import Button, LabelFrame, Label, Entry

        self.paramFrame = LabelFrame(self.root, text="参数")
        self.paramLabels = [Label(self.paramFrame, text=self.NAMES[i]) for i in range(len(self.NAMES))]
        self.paramVars = [StringVar(value=str(self.PARAMS[i])) for i in range(len(self.NAMES))]
        self.paramEntries = [Entry(self.paramFrame, textvariable=self.paramVars[i], validate="focusout", validatecommand=lambda i=i: self.paramCallback(i), width=8) for i in range(len(self.NAMES))]

        self.controlFrame = LabelFrame(self.root, text="控制")
        self.speedLabel = Label(self.controlFrame, text="速度")
        self.speedVar = StringVar(value="0")
        self.speedEntry = Entry(self.controlFrame, textvariable=self.speedVar, validate="focusout", validatecommand=self.speedCallback, width=6)
        self.uploadButton = Button(self.controlFrame, text="上传", state="disabled", command=self.upload)
        self.startButton = Button(self.controlFrame, text="启动", state="disabled", command=self.start)
        self.resetButton = Button(self.controlFrame, text="重置", state="disabled", command=self.reset)

        self.paramFrame.pack(side="left", padx=3, pady=3)
        for i in range(len(self.NAMES)):
            self.paramLabels[i].grid(row=i, column=0, padx=3, pady=3)
            self.paramEntries[i].grid(row=i, column=1, padx=3, pady=3)

        self.controlFrame.pack(side="left", fill="y", padx=3, pady=3)
        self.speedLabel.grid(row=0, column=0, padx=3, pady=3)
        self.speedEntry.grid(row=0, column=1, padx=3, pady=3)
        self.uploadButton.grid(row=1, column=0, columnspan=2, padx=3, pady=1)
        self.startButton.grid(row=2, column=0, columnspan=2, padx=3, pady=1)
        self.resetButton.grid(row=3, column=0, columnspan=2, padx=3, pady=1)

        self.root.title("FBScope - 循迹控制")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        self.root.attributes("-toolwindow", True)
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)
        self.root.bind("<space>", lambda e: self.reset())

        if "Patrol" in self.main.Config["WINDOWPOSITION"]:
            self.root.geometry(self.main.Config["WINDOWPOSITION"]["Patrol"])

    def paramCallback(self, i):
        try:
            self.PARAMS[i] = float(self.paramVars[i].get())
        except:
            self.paramVars[i].set(str(self.PARAMS[i]))
            return False
        return True

    def speedCallback(self):
        try:
            t = int(self.speedVar.get())
            if -32768 <= t < 32768:
                return True
        except:
            self.speedVar.set("0")
        return False

    def setActivate(self, activate: bool):
        state = ("disabled", "normal")
        self.uploadButton["state"] = self.startButton["state"] = self.resetButton["state"] = state[activate]
        self.enabled = activate

    def upload(self):
        from numpy import array

        self.main.write(self.SETPARAMS + array(self.PARAMS).astype("float32").tobytes())

    def start(self):
        for i in range(5):
            self.main.setstate.checked[i].set(True)
        self.main.write(self.main.setstate.PWM + b"\x04" + int(self.speedVar.get()).to_bytes(2, "little", signed=True))
        self.main.setstate.uploadState()

    def reset(self):
        if self.enabled:
            self.main.setstate.urgentReset()
