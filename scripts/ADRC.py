def ADRCgetMat(wo, wc, b0, dt):
    from numpy import mat, float64, concatenate, array, zeros
    from scipy.linalg import expm

    A = mat("0 1 0;0 0 1;0 0 0", float64)  # 3x3
    B = mat([0, b0, 0], float64).T  # 3x1
    C = mat("1 0 0", float64)  # 1x3
    L = mat([3 * wo, 3 * wo * wo, wo * wo * wo], float64).T  # 3x1
    A_obs_ct = A - L * C  # 3x3
    B_obs_ct = concatenate((B, L), axis=1)  # 3x2

    # 离散化
    discretization = concatenate((concatenate((A_obs_ct, B_obs_ct), axis=1), zeros((2, 5), float64)))
    discretization_exp = expm(discretization * dt)
    A_obs_dt = discretization_exp[0:3, 0:3]
    B_obs_dt = discretization_exp[0:3, 3:5]
    tmp = array((wc * wc, wc + wc, b0), float64)
    res = concatenate((A_obs_dt.flatten(), B_obs_dt.flatten(), tmp))
    return res


class ADRC:
    def __init__(self, main) -> None:
        from tkinter import Toplevel

        self.main = main
        self.root = Toplevel(self.main.root)
        self.setProperty()

    def setProperty(self) -> None:
        from tkinter import Canvas, StringVar
        from tkinter.ttk import LabelFrame, Button, Label, Entry

        # names = ("L1", "L2", "R1", "R2", "TURN")
        names = ("L1", "L2", "R1", "R2")
        texts = ("ωo:", "ωc:", "b0:", "dt:")

        self.frames = [LabelFrame(self.root, text=names[i]) for i in range(len(names))]
        self.texts = [[Label(self.frames[i], text=texts[j]) for j in range(4)] for i in range(len(names))]
        self.strings = [[StringVar() for j in range(4)] for i in range(len(names))]
        self.entries = [[Entry(self.frames[i], textvariable=self.strings[i][j], validate="focusout", validatecommand=lambda i=i, j=j: self.entryCallback(i, j), width=10,) for j in range(4)] for i in range(len(names))]
        self.uploadButtons = [Button(self.frames[i], text="上传", state="disabled", command=lambda i=i: self.upload(i)) for i in range(len(names))]
        self.saveButton = Button(self.root, text="存入cpp", command=self.generate, width=8)
        self.dirStr = StringVar()
        self.dirEntry = Entry(self.root, textvariable=self.dirStr)
        self.dirButton = Button(self.root, text="打开", width=4, command=self.dirCall)

        self.root.title("FBScope - ADRC")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)

        for i in range(len(names)):
            self.frames[i].pack(padx=3)
            for j in range(4):
                self.texts[i][j].pack(side="left")
                self.entries[i][j].pack(side="left", padx=3, pady=1)
            self.uploadButtons[i].pack(padx=3)

        self.saveButton.pack(side="left", padx=3, pady=3)
        self.dirEntry.pack(side="left", expand=True, fill="x")
        self.dirButton.pack(side="left", padx=3)

        self.getConfig()
        self.setConfig()

    def getConfig(self):
        # keys = ("L1", "L2", "R1", "R2", "TURN")
        keys = ("L1", "L2", "R1", "R2")
        self.main.Config
        self.Config = [self.main.Config["ADRC"][key] for key in keys]
        self.HEAD = self.main.Config["ADRC"]["HEAD"]
        self.dirStr.set(self.main.Config["ADRC"]["DIR"])

    def setConfig(self):
        for i in range(len(self.frames)):
            for j in range(4):
                self.strings[i][j].set(str(self.Config[i][j]))

    def entryCallback(self, i, j):
        try:
            self.Config[i][j] = float(self.strings[i][j].get())
            return True
        except:
            self.strings[i][j].set(str(self.Config[i][j]))
            return False

    def upload(self, i):
        self.main.write(self.HEAD + bytes([i]) + ADRCgetMat(*self.Config[i]).tobytes())
        self.root.bell()

    def dirCall(self):
        from tkinter.filedialog import askdirectory

        dirGet = askdirectory(initialdir=self.dirStr.get())
        if dirGet:
            self.dirStr.set(dirGet)

    def generate(self):
        # names = ["AdrcMatL1", "AdrcMatL2", "AdrcMatR1", "AdrcMatR2", "AdrcMatTurn"]
        names = ["AdrcMatL1", "AdrcMatL2", "AdrcMatR1", "AdrcMatR2"]
        try:
            with open(self.dirStr.get() + "\ADRCMat.cpp", "w") as f:
                f.write('#include "initSettings.h"\ntypedef unsigned long long uint64;  // clang-format off')
                for name, li in zip(names, self.Config):
                    tmp = ADRCgetMat(*li).tobytes().hex(" ", 8).split()
                    tmp = ["".join(a[i : i + 2] for i in range(14, -1, -2)) for a in tmp]
                    f.write("\n__ADJUSTABLE_E uint64 " + name + "[18]{0x" + ",0x".join(tmp) + "};")
            self.main.Config["ADRC"]["DIR"] = self.dirStr.get()
        except:
            self.dirStr.set("地址无效")
        self.root.bell()

    def setActivate(self, activate: bool):
        state = ("disabled", "normal")
        for button in self.uploadButtons:
            button["state"] = state[activate]

