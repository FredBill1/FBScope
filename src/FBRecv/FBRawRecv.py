import queue
from typing import List, Callable, Optional
import struct
import threading
import sys, os, os.path

sys.path.append(os.path.dirname(__file__))
from FBRecv import FBRecv


class FBRawRecv(FBRecv):
    def __init__(self, queue_size: int = 10):
        super().__init__(queue_size=queue_size)
        self._recvCBs: List[Callable[[bytes], None]] = []

        self.cnt = 1

        self._configLock = threading.Lock()

    def setConfig(self, cnt: Optional[int] = None) -> None:
        with self._configLock:
            if cnt is not None:
                self.cnt = cnt

    def start(self) -> None:
        super().start()

        self._recvThread = threading.Thread(target=self._recvThreadEntry)
        self._recvThread.daemon = True
        self._recvThread.start()

    def shutdown(self) -> None:
        super().shutdown()

    def recv(self) -> bytes:
        with self._configLock:
            cnt = self.cnt
        try:
            self._waitHeader()
            if not self._running:
                return None
            res = bytearray(cnt)
            for i in range(0, cnt, 32):
                for j in range(i, min(i + 32, cnt)):
                    cur = self.getchar(as_int=True)
                    if cur is None:
                        return None
                    res[j] = cur
                with self._configLock:
                    if cnt != self.cnt:
                        return None
            return bytes(res)
        except queue.Empty:
            return None

    def registerRecvCallback(self, worker: Callable[[bytes], None]) -> None:
        if self._running:
            raise RuntimeError("开始运行后不能注册新的回调函数")
        self._recvCBs.append(worker)

    def _recvThreadEntry(self) -> None:
        while self._running:
            data = self.recv()
            if data is None:
                continue
            for cb in self._recvCBs:
                if not self._running:
                    break
                cb(data)


__all__ = ["FBRawRecv"]
