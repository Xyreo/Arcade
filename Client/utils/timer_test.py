import tkinter as tk
import tkinter.ttk as ttk
from timer import Timer
import time
import threading

root = tk.Tk()
root.geometry("400x400")
b = Timer(100)


def thing():
    while True:
        a = round(b.time_left(), 2)
        if a < 0:
            break  # ! Do things here
        if a < 0.01:
            min, sec, ms = 0, 0, 0
        min, sec, ms = int(a // 60), int(a % 60), int(a * 100 % 100)
        tim.configure(text="{:02d}:{:02d}:{:02d}".format(min, sec, ms))
        time.sleep(0.005)


tim = tk.Label(root, text="00:00:00", font="consolas 20")
tim.pack()
t = threading.Thread(target=thing, daemon=True)
t.start()


tk.Button(root, text="pause", command=b.pause).pack()
tk.Button(root, text="resume", command=b.resume).pack()
tk.Button(root, text="start", command=b.start).pack()


root.mainloop()
