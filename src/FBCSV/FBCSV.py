import csv
import threading
from queue import SimpleQueue
from typing import Iterable


class FBCSVWriter:
    def __init__(self, filename: str, appends: bool = False):
        self._file = open(filename, "a" if appends else "w", newline="")
        self._writer = csv.writer(self._file)
        self._Q = SimpleQueue()
        self._thread = threading.Thread(target=self._writeEntry)
        self._running = True
        self._thread.start()

    def _writeEntry(self):
        while True:
            data = self._Q.get()
            if data is None:
                if self._running:
                    continue
                break
            self._writer.writerow(data)

    def write(self, data: Iterable[str]):
        if not self._running:
            raise RuntimeError("Writer is closed")
        self._Q.put(data)

    def close(self):
        if self._running:
            self._running = False
            self._Q.put(None)
            self._thread.join()
            self._file.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


class FBCSVReader:
    def __init__(self, filename: str):
        self._file = open(filename, "r", newline="")
        self._reader = csv.reader(self._file)

    def __enter__(self):
        self._file.__enter__()
        return self

    def __exit__(self, *_):
        self._file.close()

    def __iter__(self):
        return self._reader.__iter__()

    def __next__(self):
        return self._reader.__next__()

    def close(self):
        self._file.close()


__all__ = ["FBCSVWriter", "FBCSVReader"]

if __name__ == "__main__":
    from time import sleep
    from random import randint

    with FBCSVWriter("test.csv") as writer:

        def testEntry():
            for i in range(10):
                writer.write([threading.current_thread().name.split("-")[-1]] + [i] * randint(1, 3))
                sleep(0.1)

        threads = [threading.Thread(target=testEntry) for _ in range(20)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

    with FBCSVReader("test.csv") as reader:
        print([row for row in reader])
