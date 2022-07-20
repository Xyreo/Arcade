import threading
import time


class Timer(threading.Thread):
    def __init__(self, total):
        super().__init__(target=self, daemon=True)
        self.isPaused = False
        self.counter = total
        self.lock = threading.Lock()
        self.comp_time = time.perf_counter()
        self.prec = 300

    def run(self):
        while True:
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


if __name__ == "__main__":
    t = Timer(100)
    t.start()

    b = time.perf_counter()
    c = 1
    while True:
        a = round(t.time_left(), 2)
        if a < 0:
            break
        if a < 0.01:
            min, sec, ms = 0, 0, 0
        min, sec, ms = int(a // 60), int(a % 60), int(a * 100 % 100)
        print("{:02d}:{:02d}:{:02d}".format(min, sec, ms), sep=":", end="\r")
        time.sleep(0.005)
        c += 1
    print()
    print(time.perf_counter() - b - 0.01)
    print(c)
