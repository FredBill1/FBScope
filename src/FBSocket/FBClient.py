import socket
from typing import Tuple
import time
import queue
import threading
import os.path, sys

sys.path.append(os.path.join(os.path.dirname(__file__)))
from CONFIG import HOST, PORT
from FBSocketBase import FBSocketBase


class FBClient(FBSocketBase):
    def __init__(self):
        super().__init__()
        self._sock: socket.socket = None

        self._sendBuf = queue.Queue(10)

    def _tryConnect(self) -> None:
        if self._running:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            first = True
            while self._running:
                if first:
                    first = False
                    self._log("尝试连接到", "%s:%d" % self.addr)
                try:
                    self._sock.connect(self.addr)
                    self._sock.sendall(b"")
                    break
                except ConnectionError:
                    time.sleep(0.5)
                except OSError:
                    break
            if self._running:
                self._log("连接成功")

    def _tryWithReconnect(self, func: callable):
        if self._sock is None:
            self._tryConnect()
        while self._running:
            try:
                return func()
            except ConnectionError:
                self._log("连接已断开")
                self._tryConnect()
            except OSError:
                return None
        return None

    def _sendThreadEntry(self) -> None:
        while self._running:
            data = self._sendBuf.get()
            if not self._running or data is None:
                break
            self._tryWithReconnect(lambda: self._sock.sendall(data))

    def start(self, addr: Tuple[str, int] = (HOST, PORT)) -> None:
        self.addr = addr
        self._running = True

        self._sendThread = threading.Thread(target=self._sendThreadEntry)
        self._sendThread.daemon = True
        self._sendThread.start()

        self._startRecvThread()
        self._log("客户端启动")

    def send(self, data: bytes) -> None:
        self._instantPut(self._sendBuf, data)

    def recv(self) -> bytes:
        return self._tryWithReconnect(lambda: self._sock.recv(1024))

    def shutdown(self) -> None:
        self._running = False
        try:
            self._sendBuf.put(None, timeout=0.5)  # 发送空数据，结束线程
        except queue.Full:
            pass
        self._sendThread.join()

        if self._sock is not None:
            self._sock.close()

        self._joinRecvThread()
        self._log("客户端终止")


__all__ = ["FBClient"]

if __name__ == "__main__":
    client = FBClient()
    client.registerRecvCallback(lambda data: print("接收:", data))
    client.start()

    while True:
        s = input()
        if s == "q":
            break
        client.send(s.encode("ascii"))

    client.shutdown()
