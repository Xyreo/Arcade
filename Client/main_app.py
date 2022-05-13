import random
import threading
import tkinter as tk
import tkinter.ttk as ttk
from time import sleep
from tkinter import messagebox as msgb

import mysql.connector as msc
from PIL import Image, ImageOps, ImageTk


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
            command=lambda: self.join_room(parent, game),
        )
        self.join_button.place(relx=0.5, rely=0.4, anchor="center")

        self.create_button = ttk.Button(
            parent,
            text="Create A Room",
            style="my.TButton",
            command=lambda: self.create_room(parent, game),
        )
        self.create_button.place(relx=0.5, rely=0.6, anchor="center")

    def join_room(self, parent, game):
        if game == "Chess":
            max_players = 2
        elif game == "Monopoly":
            max_players = 4

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
            command=self.join_frame.place_forget,
        ).place(relx=0.01, rely=0.01, anchor="nw")

        self.bind("<Escape>", lambda a: self.join_frame.place_forget())

        scroll = ttk.Scrollbar(self.join_frame, orient="vertical")
        scroll.place(relx=1, rely=0, anchor="ne", relheight=1)

        self.rooms_tree = ttk.Treeview(
            self.join_frame,
            columns=("Room", "Host", "Players"),
            yscrollcommand=scroll.set,
        )

        scroll.configure(command=self.rooms_tree.yview)

        self.rooms_tree.column(
            "#0",
            width=10,
        )
        self.rooms_tree.column(
            "Room",
            width=self.screen_width // 10,
            anchor="center",
            minwidth=self.screen_width // 10,
        )
        self.rooms_tree.column(
            "Host",
            width=self.screen_width // 10,
            anchor="center",
            minwidth=self.screen_width // 10,
        )
        self.rooms_tree.column(
            "Players",
            width=self.screen_width // 10,
            anchor="center",
            minwidth=self.screen_width // 10,
        )

        self.rooms_tree.heading("#0", text="")
        self.rooms_tree.heading("Room", text="Room No.", anchor="center")
        self.rooms_tree.heading("Host", text="Host", anchor="center")
        self.rooms_tree.heading("Players", text="No. of Players", anchor="center")

        for i, j in self.rooms[game].items():
            if j["Players"] != max_players:
                self.rooms_tree.insert(
                    parent="",
                    index="end",
                    iid=i,
                    text="",
                    values=(i, j["Host"], j["Players"]),
                )

        self.rooms_tree.place(
            relx=0, rely=0.05, anchor="nw", relheight=0.9, relwidth=0.96
        )

        tk.Button(
            self.join_frame,
            text="Join",
            font=("times", 13),
            command=lambda: self.join_selected_room(self.rooms_tree.selection()[0]),
        ).place(relx=0.96, rely=1, anchor="se")

    def join_selected_room(self, room):
        print("Joining", room)

    def create_room(self, parent, game):
        print("Creating", game)


if __name__ == "__main__":
    root = tk.Tk()
    arc = arcade()
    arc.start_arcade()
    root.mainloop()
