from client_framework import Client
from chess_multiplayer import Chess
import threading
import tkinter as tk
import os
from dotenv import load_dotenv

load_dotenv()


class Suffering:
    def __init__(self, a) -> None:
        # self.c = Client(("167.71.231.52", 6789))
        self.c = Client((os.getenv("SERVER"), os.getenv("PORT")))
        self.app: Chess = None
        self.GUI()

    def start_chess(self, color, update):
        self.app = Chess(color, update)
        self.app.mainloop()

    def recv(self, x):
        global app
        print(x)
        if x[0] == "ROOM":
            if x[1] == "START":
                pass

        elif x[0] == "CHESS":
            if x[1] == "START":
                t = threading.Thread(target=self.start_chess, args=(x[2], self.c.send))
                t.start()
                self.root.withdraw()
            elif x[1] == "MOVE":
                self.app.move(sent=x[2], multi=True)

    def send(self):
        a = self.var.get()
        l = a.split()
        print(l)
        if l[0] == "ROOM":
            if l[1] == "CREATE":
                self.c.create_room()
            elif l[1] == "JOIN":
                self.c.join_room(int(l[2]))
            if l[1] == "LIST":
                self.c.fetch_rooms()
            if l[1] == "START":
                self.c.start()
                self.c.send(("CHESS", "START", "WHITE"))

    def GUI(self):
        self.c.startrecv(self.recv)

        self.root = tk.Tk()
        self.root.title("TicTacToe")
        self.root.geometry("400x400")
        self.var = tk.StringVar()
        self.submit = tk.Button(
            self.root,
            text="Submit",
            font=("Helvetica", 20),
            height=1,
            width=10,
            command=self.send,
        )
        self.inputtxt = tk.Entry(self.root, textvariable=self.var, width=300)
        self.submit.pack()
        self.inputtxt.pack()
        self.root.mainloop()


if __name__ == "__main__":
    a = Suffering(1)
