import serial
from serial.tools.list_ports import comports
from serial.threaded import Protocol, ReaderThread
import os.path, sys
import threading
from typing import List

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from FBSocket import FBServer, FBClient


class FBSerial:
    def __init__(self, isServer: bool = True):
        self._client = FBServer() if isServer else FBClient()
        self._client.registerRecvCallback(self._send)

        self._serThread: ReaderThread = None

        self._connected = threading.Event()
        self._running = True

        self._conCB: List[callable] = []
        self._disconCB: List[callable] = []

    @staticmethod
    def _protocalFactory(master: "FBSerial"):
        class PrintLines(Protocol):
            def connection_made(self, transport):
                for cb in master._conCB:
                    cb()
                self.port = transport.serial.port
                print(f"[FBSerial]连接建立: {self.port}")
                master._connected.set()

            def data_received(self, data):
                master._client.send(data)

            def connection_lost(self, exc):
                master._connected.clear()
                master._serThread = None
                for cb in master._disconCB:
                    cb()
                print(f"[FBSerial]连接断开: {self.port}")

        return PrintLines

    def _send(self, data: bytes) -> None:
        if self._running:
            self._connected.wait()
        if not self._running:
            return
        try:
            self._serThread.write(data)
        except:
            pass

    def start(self):
        self._running = True
        self._client.start()

    def shutdown(self) -> None:
        self._running = False
        self.close()
        self._client.shutdown()

    def connect(self, port, baudrate=115200):
        self.close()
        ser = serial.Serial(port=port, baudrate=baudrate)
        self._serThread = ReaderThread(ser, self._protocalFactory(self))
        self._serThread.start()

    def close(self) -> None:
        if self._serThread is not None:
            self._serThread.close()

    def registerConnectCallback(self, func: callable) -> None:
        self._conCB.append(func)

    def registerDisconnectCallback(self, func: callable) -> None:
        self._disconCB.append(func)


if __name__ == "__main__":
    ser = FBSerial()
    ser.start()
    ser.connect("COM4")

    input()

    ser.shutdown()
