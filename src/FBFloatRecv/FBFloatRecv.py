import queue
from typing import List, Callable, Optional
import struct
import threading


class FBFloatRecv:
    def __init__(self):
        self._inputBuf = queue.Queue(10)
        self._recvCBs: List[Callable[[List[float]], None]] = []
        self._running = False

        self._curBuf = b""
        self._curIdx = 0

        self.HEADER = b"\x00\xff\x80\x7f"
        self.cnt = 1
        self.bits = 4
        self.checksum = True
        self.timeout = 0.5
        self._configLock = threading.Lock()

    def input(self, data: bytes) -> None:
        self._instantPut(self._inputBuf, data)

    def setConfig(
        self, cnt: Optional[int] = None, bits: Optional[int] = None, checksum: Optional[bool] = None,
    ) -> None:
        with self._configLock:
            if cnt is not None:
                self.cnt = cnt
            if bits is not None:
                if bits not in (4, 8):
                    raise ValueError("bits 只能是 4 或 8")
                self.bits = bits
            if checksum is not None:
                self.checksum = checksum

    def start(self) -> None:
        self._running = True

        self._recvThread = threading.Thread(target=self._recvThreadEntry)
        self._recvThread.daemon = True
        self._recvThread.start()

    def shutdown(self) -> None:
        self._running = False
        # self._recvThread.join()

    def _waitHeader(self) -> None:
        tmp = [0] * 4
        i = 0
        while self._running:
            tmp[i] = self.getchar(as_int=True)
            for j in range(4):
                if tmp[(i + j + 1) & 3] != self.HEADER[j]:
                    break
            else:
                return
            i = (i + 1) & 3

    def recv(self) -> List[float]:
        with self._configLock:
            cnt = self.cnt
            bits = self.bits
            checksum = self.checksum
        try:
            self._waitHeader()
            if not self._running:
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
                    if self.cnt != cnt or self.bits != bits or self.checksum != checksum:
                        return None
            return res
        except queue.Empty:
            return None

    def getchar(self, as_int: bool = False, timeout: bool = True) -> bytes:
        while self._running and self._curIdx >= len(self._curBuf):
            self._curBuf = self._inputBuf.get(timeout=self.timeout if timeout else None)
            self._curIdx = 0
        if not self._running:
            return None
        res = self._curBuf[self._curIdx] if as_int else self._curBuf[self._curIdx : self._curIdx + 1]
        self._curIdx += 1
        return res

    def _instantPut(self, Que: queue.Queue, data) -> None:
        while self._running:
            try:
                Que.put_nowait(data)
                return
            except queue.Full:
                try:
                    Que.get_nowait()
                except queue.Empty:
                    pass

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
