import socketserver
import socket
import threading
import queue
from typing import Dict, Tuple
import os.path, sys

sys.path.append(os.path.join(os.path.dirname(__file__)))
from CONFIG import HOST, PORT
from FBSocketBase import FBSocketBase


class FBServer(FBSocketBase):
    def __init__(self):
        super().__init__()
        self._clients: Dict[Tuple[str, int], Tuple[socket.socket, threading.Lock]] = {}
        self._clientsLock = threading.Lock()

        self._recvBuf = queue.Queue(10)

    @staticmethod
    def _ignoreConnectionError(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ConnectionError:
                pass
            except OSError:
                pass

        return wrapper

    @staticmethod
    def _HandlerFactory(master: "FBServer"):
        class Handler(socketserver.BaseRequestHandler):
            def setup(self):
                master._clientsLock.acquire()
                master._clients[self.client_address] = [self.request, threading.Lock()]
                master._clientsLock.release()
                master._log("连接建立:", "%s:%d" % self.client_address)

            @FBServer._ignoreConnectionError
            def handle(self):
                while master._running:
                    data = self.request.recv(1024)
                    if not data:
                        break
                    master._instantPut(master._recvBuf, data)

            def finish(self):
                with master._clientsLock:
                    if self.client_address in master._clients:
                        client, lock = master._clients[self.client_address]
                        master._tryClose(client)
                        del master._clients[self.client_address]
                master._log("连接断开: %s:%d" % self.client_address)

        return Handler

    def start(self, addr: Tuple[str, int] = (HOST, PORT)) -> None:
        self._running = True

        class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
            ...

        self._server = ThreadedTCPServer(addr, self._HandlerFactory(self))
        self._serverThread = threading.Thread(target=self._server.serve_forever)
        # self._serverThread.daemon = True
        self._serverThread.start()

        self._startRecvThread()
        self._log("服务端启动, 地址: %s:%d" % addr)

    def shutdown(self) -> None:
        self._running = False
        try:
            self._recvBuf.put(None, timeout=0.5)  # 发送空数据，结束线程
        except queue.Full:
            pass

        with self._clientsLock:
            for client, lock in self._clients.values():
                self._tryClose(client)

        self._server.shutdown()
        # self._serverThread.join()
        self._server.server_close()
        # self._joinRecvThread()
        self._log("服务端终止")

    def _doSendAll(self, data: bytes, client: socket.socket, lock: threading.Lock):
        with lock:
            self._ignoreConnectionError(client.sendall)(data)

    def send(self, data) -> None:
        with self._clientsLock:
            clients = list(self._clients.values())
        tasks = [
            (lambda c=client, l=lock: self._doSendAll(data, c, l)) for client, lock in clients if not lock.locked()
        ]
        threads = [threading.Thread(target=task) for task in tasks]
        for thread in threads:
            # thread.setDaemon(True)
            thread.start()
        for (client, lock), thread in zip(clients, threads):
            thread.join(0.5)
            if thread.is_alive():
                self._tryClose(client)

    def recv(self) -> bytes:
        if not self._running:
            return None
        return self._recvBuf.get()


__all__ = ["FBServer"]

if __name__ == "__main__":
    server = FBServer()
    server.registerRecvCallback(lambda data: print("接收:", data.hex(" ", 1)))
    server.start()

    while True:
        s = input()
        if s == "q":
            break
        server.send(s.encode("ascii"))

    server.shutdown()
