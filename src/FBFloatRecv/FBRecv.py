import queue


class FBRecv:
    HEADER = b"\x00\xff\x80\x7f"

    def __init__(self, queue_size: int = 10):
        self._inputBuf = queue.Queue(queue_size)
        self._running = False

        self.timeout = 0.5

        self._curBuf = b""
        self._curIdx = 0

    def input(self, data: bytes) -> None:
        self._instantPut(self._inputBuf, data)

    def start(self) -> None:
        self._running = True

    def shutdown(self) -> None:
        self._running = False

    def getchar(self, as_int: bool = False, timeout: bool = True) -> bytes:
        while self._running and self._curIdx >= len(self._curBuf):
            self._curBuf = self._inputBuf.get(timeout=self.timeout if timeout else None)
            self._curIdx = 0
        if not self._running:
            return None
        res = self._curBuf[self._curIdx] if as_int else self._curBuf[self._curIdx : self._curIdx + 1]
        self._curIdx += 1
        return res

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
