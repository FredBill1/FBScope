from typing import List, Callable, Tuple
import threading
import queue


class FBSocketBase:
    def __init__(self):
        self._running = False
        self._recvCBs: List[Callable[[bytes], None]] = []

    def start(self, addr: Tuple[str, int]) -> None:
        raise NotImplementedError()

    def shutdown(self) -> None:
        raise NotImplementedError()

    def send(self, data: bytes) -> None:
        raise NotImplementedError()

    def recv(self) -> bytes:
        raise NotImplementedError()

    def _recvThreadEntry(self) -> None:
        while self._running:
            data = self.recv()
            if data is None:
                break
            for cb in self._recvCBs:
                if not self._running:
                    break
                cb(data)

    def _startRecvThread(self) -> None:
        if self._recvCBs:
            self._recvThread = threading.Thread(target=self._recvThreadEntry)
            self._recvThread.daemon = True
            self._recvThread.start()

    def _joinRecvThread(self) -> None:
        if self._recvCBs:
            self._recvThread.join()

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

    def registerRecvCallback(self, worker: Callable[[bytes], None]) -> None:
        if self._running:
            raise RuntimeError("开始运行后不能注册新的回调函数")
        self._recvCBs.append(worker)


__all__ = ["FBSocketBase"]
