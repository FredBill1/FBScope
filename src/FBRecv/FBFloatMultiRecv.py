import queue
from typing import List, Callable, Optional, Dict, Tuple, Iterable
import struct
import threading
import sys, os, os.path
from collections import defaultdict
from dataclasses import dataclass, astuple

sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from FBRecv import FBRecv
from FBCSV import FBCSVReader


@dataclass
class FBFloatMultiRecvCfg:
    cnt: int = 1
    bits: int = 4
    checksum: bool = True


class FBFloatMultiRecv(FBRecv):
    def __init__(self, queue_size: int = 10):
        super().__init__(queue_size=queue_size)
        self._recvCBs: Dict[int, List[Callable[[List[float]], None]]] = defaultdict(list)
        self._recvCfgs: Dict[int, FBFloatMultiRecvCfg] = defaultdict(FBFloatMultiRecvCfg)
        self._configLock = threading.Lock()

    def setConfig(
        self, id: int, cnt: Optional[int] = None, bits: Optional[int] = None, checksum: Optional[bool] = None,
    ) -> None:
        with self._configLock:
            cfg = self._recvCfgs[id]
            if cnt is not None:
                cfg.cnt = cnt
            if bits is not None:
                if bits not in (4, 8):
                    raise ValueError("bits 只能是 4 或 8")
                cfg.bits = bits
            if checksum is not None:
                cfg.checksum = checksum

    def start(self) -> None:
        super().start()

        self._recvThread = threading.Thread(target=self._recvThreadEntry)
        self._recvThread.daemon = True
        self._recvThread.start()

    def recv(self) -> Tuple[int, List[float]]:
        try:
            self._waitHeader()
            if not self._running:
                return None
            id = self.getchar(as_int=True)
            with self._configLock:
                if not (id in self._recvCBs):
                    return None
                cnt, bits, checksum = astuple(self._recvCfgs[id])
            res = [None] * cnt
            for i in range(cnt):
                tmp = [None] * bits
                for j in range(bits):
                    tmp[j] = self.getchar(as_int=True)
                    if tmp[j] is None:
                        return None
                if checksum and sum(tmp) & 255 != self.getchar(as_int=True):
                    return None
                res[i] = struct.unpack("f" if bits == 4 else "d", bytes(tmp))[0]
                with self._configLock:
                    if (cnt, bits, checksum) != astuple(self._recvCfgs[id]):
                        return None
            return id, res
        except queue.Empty:
            return None

    def registerRecvCallback(self, id: int, worker: Callable[[List[float]], None]) -> None:
        if self._running:
            raise RuntimeError("开始运行后不能注册新的回调函数")
        if not 0 <= id <= 255:
            raise ValueError("id 只能是 0~255")
        self._recvCBs[id].append(worker)

    def _recvThreadEntry(self) -> None:
        while self._running:
            data = self.recv()
            if data is None:
                continue
            id, data = data
            for cb in self._recvCBs[id]:
                if not self._running:
                    break
                cb(data)

    def loadCfg(self, cfgs: Iterable[Tuple[int, int, int, int]]):
        for cfg in cfgs:
            self.setConfig(*map(int, cfg))  # id, cnt, bits, checksum

    def loadCfgFromCSV(self, filename: str):
        with FBCSVReader(filename) as reader:
            self.loadCfg(reader)


__all__ = ["FBFloatMultiRecv", "FBFloatMultiRecvCfg"]

if __name__ == "__main__":
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    from FBSocket import FBServer

    server = FBServer()
    recv = FBFloatMultiRecv()
    server.registerRecvCallback(recv.input)
    recv.registerRecvCallback(1, lambda x: print("1", x))
    recv.registerRecvCallback(2, lambda x: print("2", x))
    # recv.setConfig(1, cnt=2)
    recv.loadCfgFromCSV(os.path.join(os.path.dirname(__file__), "_FBFloatMultiRecvTestCfg.csv"))
    print(recv._recvCfgs)

    recv.start()
    server.start()

    input()

    recv.shutdown()
    server.shutdown()
