import socket
from typing import Tuple
import time
from CONFIG import HOST, PORT
from FBSocketBase import FBSocketBase
import queue
import threading


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
                    print("尝试连接到", "%s:%d" % self.addr)
                try:
                    self._sock.connect(self.addr)
                    break
                except ConnectionError:
                    time.sleep(0.5)
            print("连接成功")

    def _tryWithReconnect(self, func: callable):
        if self._sock is None:
            self._tryConnect()
        while self._running:
            try:
                return func()
            except ConnectionError:
                print("连接已断开")
                self._tryConnect()
        return None

    def _sendThreadEntry(self) -> None:
        while self._running:
            data = self._sendBuf.get()
            if not self._running or data is None:
                break
            self._tryWithReconnect(lambda: self._sock.sendall(data))

    def start(self, addr: Tuple[str, int]) -> None:
        self.addr = addr
        self._running = True

        self._sendThread = threading.Thread(target=self._sendThreadEntry)
        self._sendThread.daemon = True
        self._sendThread.start()

        self._startRecvThread()

    def send(self, data: bytes) -> None:
        self._instantPut(self._sendBuf, data)

    def recv(self) -> bytes:
        return self._tryWithReconnect(lambda: self._sock.recv(1024))

    def shutdown(self) -> None:
        self._running = False
        self._sendBuf.put(None)  # 发送空数据，结束线程
        if self._sock is not None:
            self._sock.close()

        self._sendThread.join()
        self._joinRecvThread()
        print("客户端终止")


__all__ = ["FBClient"]

if __name__ == "__main__":
    client = FBClient()
    client.registerRecvCallback(lambda data: print("接收:", str(data, "ascii")))
    client.start((HOST, PORT))

    while True:
        s = input()
        if s == "q":
            break
        client.send(s.encode("ascii"))

    client.shutdown()
