class Main:
    def __init__(self) -> None:
        from tkinter import Tk
        from serial import Serial
        from .Camera import Camera
        from .ADRC import ADRC
        from .SetState import SetState
        from .Scope import Scope

        self.Config = self.getConfig()
        self.serial = Serial(baudrate=int(self.Config["SERIAL"]["BAUD"]))

        self.root = Tk()
        # self.camera = Camera(self)
        # self.adrc = ADRC(self)
        # self.setstate = SetState(self)
        self.scope = Scope(self)
        self.setProperty()
        self.getPorts()

    def setProperty(self) -> None:
        from tkinter.ttk import LabelFrame, Combobox, Button

        self.portFrame = LabelFrame(self.root, text="端口", labelanchor="nw")
        self.portCombobox = Combobox(self.portFrame, state="readonly")
        self.refreshButton = Button(master=self.root, text="刷新", width=6, command=self.getPorts)
        self.activateButton = Button(master=self.root, text="连接", width=6, command=self.toggleConnection)
        self.quitButton = Button(master=self.root, text="退出", width=6, command=self.__onClose)

        self.root.title("FBScope - 串口选择")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        self.root.attributes("-toolwindow", True)
        self.root.protocol("WM_DELETE_WINDOW", self.__onClose)
        self.portFrame.grid(row=0, column=0, columnspan=3, padx=3, pady=3)
        self.portCombobox.pack(fill="x")
        self.refreshButton.grid(row=1, column=0, padx=3, pady=3)
        self.activateButton.grid(row=1, column=1, padx=3, pady=3)
        self.quitButton.grid(row=1, column=2, padx=3, pady=3)

    def getConfig(self):
        from os.path import dirname, realpath
        from configobj import ConfigObj
        from . import Defaults

        Dir = dirname(realpath(__file__))
        ConfigDir = Dir + "\\config.ini"
        Config = ConfigObj(ConfigDir)

        if "SERIAL" not in Config:
            Config["SERIAL"] = {}
        SERIAL = Config["SERIAL"]
        SERIAL["BAUD"] = int(SERIAL["BAUD"]) if "BAUD" in SERIAL else Defaults.BAUD
        SERIAL["SEND"] = eval(SERIAL["SEND"]) if "SEND" in SERIAL else Defaults.SEND
        SERIAL["CHECK"] = eval(SERIAL["CHECK"]) if "CHECK" in SERIAL else Defaults.CHECK

        if "CAMERA" not in Config:
            Config["CAMERA"] = {}
        CAMERA = Config["CAMERA"]
        CAMERA["HEIGHT"] = int(CAMERA["HEIGHT"]) if "HEIGHT" in CAMERA else Defaults.HEIGHT
        CAMERA["WIDTH"] = int(CAMERA["WIDTH"]) if "WIDTH" in CAMERA else Defaults.WIDTH
        CAMERA["ZOOM"] = int(CAMERA["ZOOM"]) if "ZOOM" in CAMERA else Defaults.ZOOM
        CAMERA["DIR"] = CAMERA["DIR"] if "DIR" in CAMERA else Defaults.IMGDIR
        if CAMERA["DIR"][-1] not in "/\\":
            CAMERA["DIR"] += "\\"

        if "ADRC" not in Config:
            Config["ADRC"] = {}
        ADRC = Config["ADRC"]
        ADRC["L1"] = [float(v) for v in ADRC["L1"]] if "L1" in ADRC else Defaults.ADRCL1
        ADRC["L2"] = [float(v) for v in ADRC["L2"]] if "L2" in ADRC else Defaults.ADRCL2
        ADRC["R1"] = [float(v) for v in ADRC["R1"]] if "R1" in ADRC else Defaults.ADRCR1
        ADRC["R2"] = [float(v) for v in ADRC["R2"]] if "R2" in ADRC else Defaults.ADRCR2
        ADRC["TURN"] = [float(v) for v in ADRC["TURN"]] if "TURN" in ADRC else Defaults.ADRCTURN
        ADRC["HEAD"] = eval(ADRC["HEAD"]) if "HEAD" in ADRC else Defaults.ADRCHEAD
        ADRC["DIR"] = ADRC["DIR"] if "DIR" in ADRC else Dir

        if "SETSTATE" not in Config:
            Config["SETSTATE"] = {}
        SETSTATE = Config["SETSTATE"]
        SETSTATE["RESET"] = eval(SETSTATE["RESET"]) if "RESET" in SETSTATE else Defaults.SETRESET
        SETSTATE["CHECK"] = eval(SETSTATE["CHECK"]) if "CHECK" in SETSTATE else Defaults.SETSTATE
        SETSTATE["SPEED"] = eval(SETSTATE["SPEED"]) if "SPEED" in SETSTATE else Defaults.SETSPEED
        SETSTATE["PWM"] = eval(SETSTATE["PWM"]) if "PWM" in SETSTATE else Defaults.SETPWM

        if "SCOPE" not in Config:
            Config["SCOPE"] = {}
        SCOPE = Config["SCOPE"]
        SCOPE["SAMPLECOUNT"] = int(SCOPE["SAMPLECOUNT"]) if "SAMPLECOUNT" in SCOPE else Defaults.SAMPLECOUNT
        SCOPE["LINES"] = int(SCOPE["LINES"]) if "LINES" in SCOPE else Defaults.LINES

        Config.write()
        return Config

    def read(self):
        try:
            return self.serial.read()
        except:
            self.serial.close()
            quit()

    def write(self, data: bytes):
        try:
            self.serial.write(self.Config["SERIAL"]["SEND"] + data)
        except:
            self.serial.close()
            quit()

    def getPorts(self):
        from serial.tools.list_ports import comports

        li = [str(com) for com in comports()]
        if not li:
            li = ["无可用端口"]
            self.activateButton["state"] = "disabled"
        else:
            self.activateButton["state"] = "normal"
        last = self.portCombobox.get()
        self.portCombobox["values"] = li
        self.portCombobox.current(li.index(last) if last in li else 0)

    def toggleConnection(self):
        if self.activateButton["text"] == "连接":
            self.activateButton["text"] = "断开"
            self.root["bg"] = "red"
            self.portCombobox["state"] = self.refreshButton["state"] = self.quitButton["state"] = "disabled"
            self.camera.setActivate(True)
            self.adrc.setActivate(True)
            self.setstate.setActivate(True)
            self.startCOM()
        else:
            self.activateButton["text"] = "连接"
            self.root["bg"] = "white"
            self.portCombobox["state"] = self.refreshButton["state"] = self.quitButton["state"] = "normal"
            self.camera.setActivate(False)
            self.adrc.setActivate(False)
            self.setstate.setActivate(False)
            self.serial.close()

    def startCOM(self):
        self.serial.port = self.portCombobox.get().split()[0]
        try:
            self.serial.open()
        except:
            self.getPorts()
            self.toggleConnection()
            return

    def setActivate(self, activate: bool):
        state = ("disabled", "normal")
        self.portCombobox["state"] = self.refreshButton["state"] = self.activateButton["state"] = state[activate]
        if activate:
            self.getPorts()

    def mainloop(self):
        self.root.mainloop()

    def __onClose(self):
        if self.activateButton["text"] == "连接":
            self.Config.write()
            quit()


if __name__ == "__main__":
    root = Main()
    root.mainloop()

