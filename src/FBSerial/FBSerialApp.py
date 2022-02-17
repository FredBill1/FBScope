from serial.tools.list_ports import comports
import ttkbootstrap as ttk
from FBSerial import FBSerial
from tkinter import messagebox
import threading


class FBSerialApp:
    def __init__(self):
        style = ttk.Style("cosmo")
        self._root = style.master
        self._root.title("FBScope: FBSerial")
        self._root.resizable(False, False)
        self._root.attributes("-topmost", True)
        self._root.protocol("WM_DELETE_WINDOW", self.shutdown)

        frame = ttk.LabelFrame(self._root, text="串口选择")
        frame.pack(padx=5, pady=5)
        self._portsCombo = ttk.Combobox(frame, state="readonly", width=23)
        self._portsCombo.pack(side="left", padx=5, pady=5)

        self._conButton = ttk.Button(frame, text="连接", command=self._connect)
        self._refreshButton = ttk.Button(frame, text="刷新", command=self._getPorts)
        self._conButton.pack(side="left", padx=5, pady=5)
        self._refreshButton.pack(side="left", padx=5, pady=5)

        self._prePort = None
        self._connected = False

        self._ser = FBSerial()
        self._ser.registerConnectCallback(self._conCB)
        self._ser.registerDisconnectCallback(self._disconCB)

    def _toggleConnect(self):
        if not self._connected:
            idx = self._portsCombo.current()
            self._prePort = self.descs[idx]
            port = self.ports[idx]
            try:
                self._ser.connect(port)
            except Exception as e:
                messagebox.showerror("错误", f"连接失败:\n{e}", master=self._root)
                self._conButton["text"] = "连接"
                self._portsCombo["state"] = "readonly"
                self._refreshButton["state"] = "!disabled"
                self._connected = False
                self._getPorts()
        else:
            self._connected = False
            self._ser.close()

    def _connect(self):
        self._conButton["state"] = "disabled"
        self._conButton["text"] = "等待"
        self._portsCombo["state"] = "disabled"
        self._refreshButton["state"] = "disabled"
        self._toggleConnect()

    def _conCB(self):
        self._conButton["state"] = "!disabled"
        self._conButton["text"] = "断开"
        self._connected = True

    def _disconCB(self):
        if self._connected:
            threading.Thread(target=lambda: messagebox.showwarning("警告", "与串口断开连接", master=self._root)).start()
            self._connected = False
        self._conButton["text"] = "连接"
        self._portsCombo["state"] = "readonly"
        self._refreshButton["state"] = "!disabled"
        self._getPorts()

    def _getPorts(self):
        if self._connected:
            return
        ports = [[port, desc] for port, desc, _ in comports()]
        self.ports = [port for port, _ in ports]
        self.descs = [desc for _, desc in ports]
        if not ports:
            self._portsCombo["values"] = ["无可用端口"]
            self._conButton["state"] = "disabled"
        else:
            self._portsCombo["values"] = self.descs
            self._conButton["state"] = "!disabled"
        if self._prePort in self.descs:
            self._portsCombo.current(self.descs.index(self._prePort))
        else:
            self._portsCombo.current(0)

    def mainloop(self):
        self._getPorts()
        self._ser.start()
        self._root.mainloop()

    def shutdown(self):
        self._connected = False
        self._ser.shutdown()
        self._root.destroy()


if __name__ == "__main__":
    app = FBSerialApp()
    app.mainloop()
