import json
import tkinter as tk
import tkinter.ttk as ttk
from time import sleep
from tkinter import messagebox as msgb

from PIL import Image, ImageOps, ImageTk

from client_framework import Client

# TODO Confirmation Popups, Delete Room
class arcade(tk.Toplevel):
    def __init__(self):
        super().__init__()
        self.initialize()
        self.create_window()
        self.notebook()
        self.chess_tab()
        self.monopoly_tab()

        self.room_frame = None
        self.lobby_frame = None

    def initialize(self):
        self.rooms = {
            "CHESS": [
                {
                    "id": "123",
                    "host": "456",
                    "settings": {},
                    "members": [{"name": "die1", "puid": "456"}],
                },
            ],
            "MNPLY": [
                {
                    "id": "345",
                    "host": "876",
                    "settings": {},
                    "members": [{"name": "die1", "puid": "456"}],
                }
            ],
        }

        self.current_room = None

        self.cobj = Client(("localhost", 6778), self.event_handler)
        self.cobj.send(("Pramit"))

    def pprint(self, d):
        print(json.dumps(d, indent=4))

    def event_handler(self, msg):
        dest = msg[0]
        print("Recv:", msg)
        if dest == "NAME":
            self.me = msg[1]
        elif dest in ["CHESS", "MNPLY"]:
            if msg[1] == "INIT":
                l = self.rooms[dest]
                for i in msg[2]:
                    l.append(i)
                self.rooms.update({dest: l})
            elif msg[1] == "ROOM":
                l = self.rooms[dest]
                if msg[2] == "ADD":
                    l.append(msg[3])
                    self.rooms.update({dest: l})
                    if msg[3]["host"] == self.me:
                        self.join_selected_room(dest, msg[3])
                elif msg[2] == "REMOVE":
                    for i in l:
                        if i["id"] == msg[3]:
                            l.remove(i)
                            self.rooms.update({dest: l})
                            break
                if self.room_frame:
                    try:
                        self.room_frame.place_forget()
                    except AttributeError:
                        pass
                    self.join_room(dest, msg[3])

                elif self.lobby_frame:
                    try:
                        self.lobby_frame.place_forget()
                    except AttributeError:
                        pass
                    self.join_lobby(dest, True)

        elif dest:
            game = ""
            for i, j in self.rooms.items():
                for k in j:
                    if k["id"] == dest:
                        game = i
            l = self.rooms[game]
            room_joined = {}
            if msg[1] == "PLAYER":
                if msg[2] == "ADD":
                    for i in l:
                        if i["id"] == dest:
                            room_joined = i
                            l2 = i["members"]
                            l2.append(msg[3])
                            i.update({"members": l2})
                            break
                elif msg[2] == "REMOVE":
                    for i in l:
                        if i["id"] == dest:
                            room_joined = i
                            l2 = i["members"]
                            for j in l2:
                                if j["puid"] == msg[3]:
                                    l2.remove(j)
                                    break
                            i.update({"members": l2})
                            break

                self.rooms.update({game: l})
                if self.room_frame:
                    self.room_frame.place_forget()
                    self.join_room(game, room_joined)
                elif self.lobby_frame:
                    self.lobby_frame.place_forget()
                    self.join_lobby(game, True)

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
        self.join_create("CHESS")

    def monopoly_tab(self):
        self.monopoly_frame = tk.Frame(self.main_notebook, background="white")
        self.monopoly_frame.place(relx=0, rely=0, relheight=1, relwidth=1, anchor="nw")
        self.main_notebook.add(self.monopoly_frame, text="Monopoly")
        self.join_create("MNPLY")

    def join_create(self, game):
        button_style = ttk.Style()
        button_style.configure("my.TButton", font=("times", 20))
        if game == "CHESS":
            parent = self.chess_frame
        elif game == "MNPLY":
            parent = self.monopoly_frame

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
            command=lambda: self.create_room(game),
        )
        self.create_button.place(relx=0.5, rely=0.6, anchor="center")

    def join_lobby(self, game, updating=False):
        if not updating:
            self.send(("0", "JOIN", game.upper()))

        if game == "CHESS":
            parent = self.chess_frame
            max_players = 2
        elif game == "MNPLY":
            parent = self.monopoly_frame
            max_players = 4

        self.lobby_frame = tk.Frame(
            parent,
            width=self.screen_width / 3,
            height=self.screen_height / 1.1,
        )
        self.lobby_frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Button(
            self.lobby_frame,
            text="← BACK",
            font=("times", 10),
            highlightthickness=0,
            border=0,
            command=lambda: self.leave_lobby(game),
        ).place(relx=0.01, rely=0.01, anchor="nw")

        self.bind("<Escape>", lambda a: self.leave_lobby(game))

        scroll = ttk.Scrollbar(self.lobby_frame, orient="vertical")
        scroll.place(relx=1, rely=0, anchor="ne", relheight=1)

        self.lobby_tree = ttk.Treeview(
            self.lobby_frame,
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

        hostname = ""
        for i in self.rooms[game]:
            for j in i["members"]:
                if j["puid"] == i["host"]:
                    hostname = j["name"]
                    break

            if len(i["members"]) < max_players:
                self.lobby_tree.insert(
                    parent="",
                    index="end",
                    iid=i,
                    text="",
                    values=(i["id"], hostname, len(i["members"])),
                )

        self.lobby_tree.place(
            relx=0, rely=0.05, anchor="nw", relheight=0.9, relwidth=0.96
        )

        tk.Button(
            self.lobby_frame,
            text="Join",
            font=("times", 13),
            command=lambda: self.join_selected_room(
                game, eval(self.lobby_tree.selection()[0])
            ),
        ).place(relx=0.96, rely=1, anchor="se")

    def leave_lobby(self, game):
        self.send(("0", "LEAVE", game.upper()))
        self.lobby_frame.place_forget()
        self.lobby_frame = None

    def join_selected_room(self, game, room):
        self.send((game, "JOIN", room["id"]))
        self.current_room = room["id"]
        self.join_room(game, room)

    def create_room(self, game):

        settings = {}
        # TODO: Select Settings
        self.send((game, "CREATE", settings))

    def leave_room(self, room):
        self.send((room["id"], "LEAVE"))
        self.room_frame.place_forget()
        self.room_frame = None

    def delete_room(self, room):
        pass

    def join_room(self, game, room):
        if game == "CHESS":
            parent = self.chess_frame
        elif game == "MNPLY":
            parent = self.monopoly_frame

        hostname = ""
        for i in room["members"]:
            if i["puid"] == room["host"]:
                hostname = i["name"]
                break

        if self.me == room["host"]:
            hostname = "You"

        self.room_frame = tk.Frame(
            parent,
            width=self.screen_width / 3,
            height=self.screen_height / 1.1,
        )
        self.room_frame.place(relx=0.5, rely=0.5, anchor="center")

        if hostname == "You":
            tk.Button(
                self.room_frame,
                text="← BACK",
                font=("times", 10),
                highlightthickness=0,
                border=0,
                command=lambda: self.delete_room(room),
            ).place(relx=0.01, rely=0.01, anchor="nw")

            self.bind("<Escape>", lambda a: self.delete_room(room))
        else:
            tk.Button(
                self.room_frame,
                text="← BACK",
                font=("times", 10),
                highlightthickness=0,
                border=0,
                command=lambda: self.leave_room(room),
            ).place(relx=0.01, rely=0.01, anchor="nw")

            self.bind("<Escape>", lambda a: self.leave_room(room))

        tk.Label(
            self.room_frame,
            text=f"Room ID: {room['id']}",
            font=("times", 13),
            highlightthickness=0,
            border=0,
        ).place(relx=0.5, rely=0.05, anchor="center")

        tk.Label(
            self.room_frame,
            text=f"Host: {hostname}",
            font=("times", 13),
            highlightthickness=0,
            border=0,
        ).place(relx=0.5, rely=0.1, anchor="center")

        tk.Label(
            self.room_frame,
            text=f"Members",
            font=("times 13 underline"),
            highlightthickness=0,
            border=0,
        ).place(relx=0.5, rely=0.2, anchor="center")

        k = 1
        for i in room["members"]:
            tk.Label(
                self.room_frame,
                text=i["name"],
                font=("times", 13),
                highlightthickness=0,
                border=0,
            ).place(relx=0.5, rely=0.2 + (k / 25), anchor="center")

            k += 1

        tk.Label(
            self.room_frame,
            text=f"Settings",
            font=("times 13 underline"),
            highlightthickness=0,
            border=0,
        ).place(relx=0.5, rely=0.5, anchor="center")

        # print settings here
        if hostname == "You":
            tk.Button(
                self.room_frame,
                text="START",
                font=("times", 13),
                command=lambda: self.start_room(game, room),
            ).place(relx=0.5, rely=0.9, anchor="se")
        else:
            tk.Label(
                self.room_frame,
                text="Waiting for Host to start the game",
                font=("times", 13),
            ).place(relx=0.5, rely=0.9, anchor="se")


if __name__ == "__main__":
    root = tk.Tk()
    arc = arcade()
    arc.start_arcade()
    root.mainloop()
