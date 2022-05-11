from client_framework import Client
import tkinter as tk


def display(msg):
    print("Received:", msg)


c = Client(("localhost", 6787), display)


root = tk.Tk()
root.geometry("600x600")


def send():
    text = entry.get()
    text = tuple(text.split(","))
    print("Sent:", text)
    c.send(text)


entry = tk.Entry(root)
entry.pack()
b = tk.Button(root, command=send)
b.pack()
root.mainloop()
