class SetState:
    def __init__(self, main) -> None:
        from tkinter import Toplevel

        self.main = main
        self.root = Toplevel(self.main.root)
        self.getConfig()
        self.setProperty()

    def getConfig(self):
        self.RESET = self.main.Config["SETSTATE"]["RESET"]
        self.CHECK = self.main.Config["SETSTATE"]["CHECK"]
        self.SPEED = self.main.Config["SETSTATE"]["SPEED"]
        self.PWM = self.main.Config["SETSTATE"]["PWM"]

    def setProperty(self) -> None:
        from tkinter import BooleanVar, StringVar
        from tkinter.ttk import Checkbutton, Button, LabelFrame, Combobox, Label, Entry

        names = ["L1", "L2", "R1", "R2", "转向"]
        self.toggleFrame = LabelFrame(self.root, text="状态控制")
        self.checked = [BooleanVar(value=0) for i in range(5)]
        self.buttons = [Checkbutton(self.toggleFrame, text=names[i] + "控制器", variable=self.checked[i]) for i in range(5)]
        self.stateButton = Button(self.toggleFrame, text="上传", state="disabled", command=self.uploadState)

        self.controlFrame = LabelFrame(self.root, text="速度控制")
        self.motorLabel = Label(self.controlFrame, text="控制:")
        self.motorCombobox = Combobox(self.controlFrame, values=names, width=3, state="readonly")
        self.speedLabel = Label(self.controlFrame, text="目标:")
        self.speedVar = StringVar(value="0")
        self.speedEntry = Entry(self.controlFrame, textvariable=self.speedVar, validate="focusout", validatecommand=lambda sv=self.speedVar: self.entryCallback(sv), width=6)
        self.pwmLabel = Label(self.controlFrame, text="定值:")
        self.pwmVar = StringVar(value="0")
        self.pwmEntry = Entry(self.controlFrame, textvariable=self.pwmVar, validate="focusout", validatecommand=lambda sv=self.pwmVar: self.entryCallback(sv), width=6)
        self.speedButton = Button(self.controlFrame, text="上传速度", state="disabled", command=self.uploadSpeed)
        self.pwmButton = Button(self.controlFrame, text="上传pwm", state="disabled", command=self.uploadPwm)
        self.resetButton = Button(self.controlFrame, text="紧急重置", state="disabled", command=self.urgentReset)

        self.root.title("FBScope - 电机控制")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        self.root.attributes("-toolwindow", True)
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)

        self.toggleFrame.pack(side="left", padx=3, pady=3, expand=True, fill="y")
        for i in range(5):
            self.buttons[i].grid(row=i, column=0, padx=3, pady=3, sticky="w")
        self.stateButton.grid(row=5 + 1, column=0, padx=3, pady=1)

        self.controlFrame.pack(side="left", padx=3, pady=3, expand=True, fill="y")
        self.motorLabel.grid(row=0, column=0, padx=3, pady=3, sticky="w")
        self.motorCombobox.current(0)
        self.motorCombobox.grid(row=0, column=1, padx=3, pady=3, sticky="w")
        self.speedLabel.grid(row=1, column=0, padx=3, pady=3, sticky="w")
        self.speedEntry.grid(row=1, column=1, padx=3, pady=3, sticky="w")
        self.speedEntry.bind("<Return>", lambda e: self.uploadSpeed())
        self.pwmLabel.grid(row=2, column=0, padx=3, pady=3, sticky="w")
        self.pwmEntry.grid(row=2, column=1, padx=3, pady=3, sticky="w")
        self.pwmEntry.bind("<Return>", lambda e: self.uploadPwm())
        self.speedButton.grid(row=3, column=0, columnspan=2, padx=3, pady=1)
        self.pwmButton.grid(row=4, column=0, columnspan=2, padx=3, pady=1)
        self.resetButton.grid(row=5, column=0, columnspan=2, padx=3, pady=1)

    def entryCallback(self, sv):
        try:
            t = int(sv.get())
            if -32768 <= t < 32768:
                return True
        except:
            pass
        sv.set("0")
        return False

    def setActivate(self, activate: bool):
        state = ("disabled", "normal")
        self.stateButton["state"] = self.resetButton["state"] = self.speedButton["state"] = self.pwmButton["state"] = state[activate]

    def uploadState(self, patrol: bool = False):
        if self.stateButton["state"] == "disabled":
            return
        state = patrol << 5
        for i in range(5):
            state |= self.checked[i].get() << i
        self.main.write(self.CHECK + bytes([state]))
        self.root.bell()

    def urgentReset(self):
        if self.resetButton["state"] == "disabled":
            return
        self.main.write(self.RESET)
        self.root.bell()

    def uploadSpeed(self):
        if self.speedButton["state"] == "disabled" or not self.entryCallback(self.speedVar):
            return
        i = self.motorCombobox.current()
        self.checked[i].set(True)
        self.uploadState()
        self.main.write(self.SPEED + bytes([i]) + int(self.speedVar.get()).to_bytes(2, "little", signed=True))

    def uploadPwm(self):
        if self.pwmButton["state"] == "disabled" or not self.entryCallback(self.pwmVar):
            return
        i = self.motorCombobox.current()
        self.checked[i].set(i == 4)
        self.uploadState()
        self.main.write(self.PWM + bytes([i]) + int(self.pwmVar.get()).to_bytes(2, "little", signed=True))
