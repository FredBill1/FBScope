import queue
from typing import List, Callable, Optional
import struct
import threading
import sys, os, os.path

sys.path.append(os.path.dirname(__file__))
from FBRecv import FBRecv


class FBFloatRecv(FBRecv):
    def __init__(self, queue_size: int = 10):
        super().__init__(queue_size=queue_size)
        self._recvCBs: List[Callable[[List[float]], None]] = []

        self.id = -1
        self.cnt = 1
        self.bits = 4
        self.checksum = True
        self._configLock = threading.Lock()

    def setConfig(
        self,
        id: Optional[int] = None,
        cnt: Optional[int] = None,
        bits: Optional[int] = None,
        checksum: Optional[bool] = None,
    ) -> None:
        with self._configLock:
            if id is not None:
                self.id = id
            if cnt is not None:
                self.cnt = cnt
            if bits is not None:
                if bits not in (4, 8):
                    raise ValueError("bits 只能是 4 或 8")
                self.bits = bits
            if checksum is not None:
                self.checksum = checksum

    def start(self) -> None:
        super().start()

        self._recvThread = threading.Thread(target=self._recvThreadEntry)
        self._recvThread.daemon = True
        self._recvThread.start()

    def shutdown(self) -> None:
        super().shutdown()

    def recv(self) -> List[float]:
        with self._configLock:
            id = self.id
            cnt = self.cnt
            bits = self.bits
            checksum = self.checksum
        try:
            self._waitHeader()
            if not self._running:
                return None
            if self.id != -1:
                if id != self.getchar(as_int=True):
                    return None
            res = [None] * cnt
            for i in range(cnt):
                tmp = [None] * bits
                for j in range(bits):
                    tmp[j] = self.getchar(as_int=True)
                    if tmp[j] is None:
                        return None
                if checksum and sum(tmp) & 255 != self.getchar(as_int=True):
                    return None
                res[i] = struct.unpack("f" if self.bits == 4 else "d", bytes(tmp))[0]
                with self._configLock:
                    if id != self.id or self.cnt != cnt or self.bits != bits or self.checksum != checksum:
                        return None
            return res
        except queue.Empty:
            return None

    def registerRecvCallback(self, worker: Callable[[List[float]], None]) -> None:
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


__all__ = ["FBFloatRecv"]

if __name__ == "__main__":
    import sys, os.path

    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    from FBSocket import FBServer

    server = FBServer()
    recv = FBFloatRecv()
    server.registerRecvCallback(recv.input)
    recv.registerRecvCallback(print)

    recv.start()
    server.start()

    input()
    recv.setConfig(cnt=2)
    input()

    recv.shutdown()
    server.shutdown()
