import time, threading

sent_time = time.perf_counter()
queue = [sent_time]


def send(msg, sleep=0):
    if sleep:
        time.sleep(sleep)
    new_time = time.perf_counter() % 10000000000000
    if queue and queue[-1] > new_time:
        t = threading.Thread(
            target=send, args=(msg,), kwargs={"sleep": queue[-1] + 0.1 - new_time}
        )
        queue.append(queue[-1] + 0.1)
        t.start()
    else:
        del queue[0]
        print(msg)


for i in range(1000):
    send(i)
