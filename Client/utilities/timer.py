import threading
import time


class Timer(threading.Thread):
    def __init__(self, total):
        super().__init__(target=self, daemon=True)
        self.total = total
        self.isPaused = False
        self.counter = self.total
        self.lock = threading.Lock()
        self.prec = 300
        self.isStopped = False

    def run(self):
        self.comp_time = time.perf_counter()
        while not self.isStopped:
            time.sleep(1 / self.prec)
            if self.isPaused:
                self.lock.acquire()
                self.comp_time = time.perf_counter()
            t = time.perf_counter()
            self.counter -= t - self.comp_time
            self.comp_time = t

    def pause(self):
        self.isPaused = True

    def resume(self):
        self.isPaused = False
        self.lock.release()

    def time_left(self):
        return self.counter

    def reset(self):
        self.counter = self.total

    def stop(self):
        self.isStopped = True

    def set_time(self, time):
        self.counter = time

    def add_time(self, time):
        self.counter += time
