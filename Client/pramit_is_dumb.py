import random
import threading
import tkinter as tk
import tkinter.ttk as ttk
from time import sleep
from tkinter import messagebox as msgb

import mysql.connector as msc
from PIL import Image, ImageOps, ImageTk

from client_framework import Client


class arcade(tk.Toplevel):
    def __init__(self):
        super().__init__()
        self.initialize()
        self.create_window()
        self.notebook()
        self.chess_tab()
        self.monopoly_tab()

    def initialize(self):
        self.rooms = {
            "Chess": {
                "1234": {"Host": "Dumbass 1", "Players": 1},
                "5678": {"Host": "Dumbass 2", "Players": 1},
                "9101": {"Host": "Dumbass 5", "Players": 2},
            },
            "Monopoly": {
                "123": {"Host": "Dumbass 3", "Players": 2},
                "456": {"Host": "Dumbass 4", "Players": 3},
                "789": {"Host": "Dumbass 6", "Players": 4},
            },
        }

        self.room = None
        self.lobby = None
        self.lobby_handler = {}
        self.room_handler = {}
        self.create_room = {}

        self.cobj = Client(("localhost", 6778), self.event_handler)
        self.cobj.send(("Pramit"))

    def event_handler(self, msg):  # ? tf is last line
        dest = msg[0]
        print("Msg:", msg)
        if dest in ["CHESS", "MNPLY"]:
            if msg[1] == "INIT":
                self.rooms = msg[3][1]
                print(self.rooms)
            elif msg[1] == "ROOM":
                if msg[2] == "ADD":
                    self.rooms.append(msg[3])
                    # self.lobby_handler[dest]["add"](msg[3])
                elif msg[2] == "DELETE":
                    self.rooms.remove(msg[3])
                    # self.lobby_handler[dest]["delete"](msg[3])
                    
        elif msg[1] == "INIT":
            self.room = dest
            self.create_room[msg[2]](dest)
            for i in msg[3]["members"]:
                self.room_handler[dest]["add"](i)

        elif dest == self.room:
            if msg[1] == "PLAYER":
                if msg[2] == "ADD":
                    self.room_handler[dest]["add"](msg[3])
                elif msg[2] == "REMOVE":
                    pass

    def join_lobby(self, lobby):
        self.send(("0", "JOIN", lobby.upper()))

    def leave_lobby(self, lobby):
        self.send(("0", "LEAVE", lobby.upper()))

    def start_room(self):
        self.send((self.room, "START"))

    def send(self, msg):
        print("Sent:", msg)
        self.cobj.send(msg)

    def create_window(self):
        self.screen_width = int(0.9 * self.winfo_screenwidth())
        self.screen_height = int(self.screen_width / 1.9)
        x_coord = self.winfo_screenwidth() // 2 - self.screen_width // 2
        y_coord = (self.winfo_screenheight() - 70) // 2 - self.screen_height // 2

        self.title("Arcade")
        self.geometry(f"{self.screen_width}x{self.screen_height}+{x_coord}+{y_coord}")
        self.config(bg="white")
        self.protocol("WM_DELETE_WINDOW", root.destroy)
        self.withdraw()

    def start_arcade(self):
        self.deiconify()
        root.withdraw()

    def notebook(self):
        self.main_notebook = ttk.Notebook(
            self, height=self.screen_height, width=self.screen_width
        )
        self.main_notebook.place(relx=0, rely=0, anchor="nw")

    def chess_tab(self):
        self.chess_frame = tk.Frame(self.main_notebook, background="white")
        self.chess_frame.place(relx=0, rely=0, relheight=1, relwidth=1, anchor="nw")
        self.main_notebook.add(self.chess_frame, text="Chess")
        self.join_create(self.chess_frame, "Chess")

    def monopoly_tab(self):
        self.monopoly_frame = tk.Frame(self.main_notebook, background="white")
        self.monopoly_frame.place(relx=0, rely=0, relheight=1, relwidth=1, anchor="nw")
        self.main_notebook.add(self.monopoly_frame, text="Monopoly")
        self.join_create(self.monopoly_frame, "Monopoly")

    def join_create(self, parent, game):
        button_style = ttk.Style()
        button_style.configure("my.TButton", font=("times", 20))

        self.join_button = ttk.Button(
            parent,
            text="Join A Room",
            style="my.TButton",
            command=lambda: self.join_lobby(game),
        )
        self.join_button.place(relx=0.5, rely=0.4, anchor="center")

        self.create_button = ttk.Button(
            parent,
            text="Create A Room",
            style="my.TButton",
            command=lambda: self.create_room(parent, game),
        )
        self.create_button.place(relx=0.5, rely=0.6, anchor="center")

    def join_room_frame(self, parent, game):
        self.join_frame = tk.Frame(
            parent,
            width=self.screen_width / 3,
            height=self.screen_height / 1.1,
        )
        self.join_frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Button(
            self.join_frame,
            text="← BACK",
            font=("times", 10),
            highlightthickness=0,
            border=0,
            command=lambda: self.quit_lobby(game),
        ).place(relx=0.01, rely=0.01, anchor="nw")

        self.bind("<Escape>", lambda: self.quit_lobby(game))

        scroll = ttk.Scrollbar(self.join_frame, orient="vertical")
        scroll.place(relx=1, rely=0, anchor="ne", relheight=1)

        self.lobby_tree = ttk.Treeview(
            self.join_frame,
            columns=("Room", "Host", "Players"),
            yscrollcommand=scroll.set,
        )

        scroll.configure(command=self.lobby_tree.yview)

        self.lobby_tree.column(
            "#0",
            width=10,
        )
        self.lobby_tree.column(
            "Room",
            width=self.screen_width // 10,
            anchor="center",
            minwidth=self.screen_width // 10,
        )
        self.lobby_tree.column(
            "Host",
            width=self.screen_width // 10,
            anchor="center",
            minwidth=self.screen_width // 10,
        )
        self.lobby_tree.column(
            "Players",
            width=self.screen_width // 10,
            anchor="center",
            minwidth=self.screen_width // 10,
        )

        self.lobby_tree.heading("#0", text="")
        self.lobby_tree.heading("Room", text="Room No.", anchor="center")
        self.lobby_tree.heading("Host", text="Host", anchor="center")
        self.lobby_tree.heading("Players", text="No. of Players", anchor="center")

        self.lobby_tree.place(
            relx=0, rely=0.05, anchor="nw", relheight=0.9, relwidth=0.96
        )

        tk.Button(
            self.join_frame,
            text="Join",
            font=("times", 13),
            command=lambda: self.send((game, "JOIN", self.lobby_tree.selection()[0])),
        ).place(relx=0.96, rely=1, anchor="se")

    def add_room(self, room, game):
        id = room["id"]
        host = room["host"]
        nply = len(room["members"])
        settings = room["settings"]
        self.lobby_tree.insert(
            parent="", index="end", iid=id, text="", values=(str(id)[:5], host, nply)
        )

    def remove_room(self, room):
        self.delete(room)

    def quit_lobby(self, game):
        self.join_frame.place_forget()
        self.leave_lobby(game)

    def join_selected_room(self, room):
        print("Joining", room)

    def create_room(self, parent, game):
        print("Creating", game)


if __name__ == "__main__":
    root = tk.Tk()
    arc = arcade()
    arc.start_arcade()
    root.mainloop()
