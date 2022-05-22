import tkinter as tk
import tkinter.ttk as ttk
import time, threading, json
from tkinter import messagebox as msgb
from PIL import Image, ImageOps, ImageTk
from client_framework import Client
from chess import Chess
from http_wrapper import Http

# TODO Confirmation Popups, Delete Room, Life


class Rooms(dict):
    def __init__(self):
        super().__init__({"CHESS": {}, "MNPLY": {}})

    def initialize(self, game, rooms):
        self[game] = {}
        for room in rooms:
            self.add_room(game, room)

    def add_room(self, game, room):
        room["members"] = {i["puid"]: i for i in room["members"]}
        self[game][room["id"]] = room

    def remove_room(self, game, id):
        del self[game][id]

    def get_rooms(self) -> dict:
        d = {}
        d.update(self["CHESS"])
        d.update(self["MNPLY"])
        return d

    def add_player(self, rid, player):
        key = "CHESS" if rid in self["CHESS"] else "MNPLY"
        self[key][rid]["members"][player["puid"]] = player

    def remove_player(self, rid, player):
        key = "CHESS" if rid in self["CHESS"] else "MNPLY"
        del self[key][rid]["members"][player]


class Arcade(tk.Toplevel):
    def __init__(self):
        super().__init__()
        self.lobby_frames = {"CHESS": None, "MNPLY": None}
        self.lobby_trees = {"CHESS": None, "MNPLY": None}
        self.room_frames = {"CHESS": None, "MNPLY": None}
        self.room_members = {"CHESS": None, "MNPLY": None}
        self.current_room = None
        self.sent_time = time.perf_counter()

    def initialize(self, name, token):
        self.login.destroy()
        self.name = name
        self.token = token
        self.rooms = Rooms()

        self.current_room = None

        self.cobj = Client(("localhost", 6778), self.event_handler)
        self.cobj.send((self.name))

        # GUI Initializing
        self.screen_width = int(0.9 * self.winfo_screenwidth())
        self.screen_height = int(self.screen_width / 1.9)
        x_coord = self.winfo_screenwidth() // 2 - self.screen_width // 2
        y_coord = (self.winfo_screenheight() - 70) // 2 - self.screen_height // 2

        self.title("Arcade")
        self.geometry(f"{self.screen_width}x{self.screen_height}+{x_coord}+{y_coord}")
        self.config(bg="white")
        self.protocol("WM_DELETE_WINDOW", root.destroy)
        self.withdraw()

        # region Notebook
        self.main_notebook = ttk.Notebook(
            self, height=self.screen_height, width=self.screen_width
        )
        self.main_notebook.place(relx=0, rely=0, anchor="nw")

        # Chess stuff
        self.chess_frame = tk.Frame(self.main_notebook, background="white")
        self.chess_frame.place(relx=0, rely=0, relheight=1, relwidth=1, anchor="nw")
        self.main_notebook.add(self.chess_frame, text="Chess")
        self.join_create("CHESS")

        # Monopoly stuff
        self.monopoly_frame = tk.Frame(self.main_notebook, background="white")
        self.monopoly_frame.place(relx=0, rely=0, relheight=1, relwidth=1, anchor="nw")
        self.main_notebook.add(self.monopoly_frame, text="Monopoly")
        self.join_create("MNPLY")
        # endregion
        self.deiconify()

    def pprint(self, d):
        print(json.dumps(d, indent=4))

    def event_handler(self, msg):
        dest = msg[0]
        print("Recv:", msg)
        room = None
        if dest == "NAME":
            self.me = msg[1]

        elif dest in ["CHESS", "MNPLY"]:
            if msg[1] == "INIT":
                self.rooms.initialize(dest, msg[2])
            elif msg[1] == "ROOM":
                room = msg[3]
                if msg[2] == "ADD":
                    self.rooms.add_room(dest, room)
                elif msg[2] == "REMOVE":
                    self.rooms.remove_room(dest, msg[3])
            elif msg[1] == "PLAYER":
                if msg[2] == "ADD":
                    self.rooms.add_player(msg[4], msg[3])
                elif msg[2] == "REMOVE":
                    self.rooms.remove_player(msg[4], msg[3])
            self.update_lobby(dest)

        elif dest == "ROOM":
            self.rooms.add_room(msg[1], msg[2])
            self.join_room(msg[1], msg[2]["id"])

        elif dest == self.current_room:
            game = "CHESS" if dest in self.rooms["CHESS"] else "MNPLY"
            if msg[1] == "PLAYER":
                if msg[2] == "ADD":
                    self.rooms.add_player(dest, msg[3])
                elif msg[2] == "REMOVE":
                    self.rooms.remove_player(dest, msg[3])
                self.update_room(game, self.rooms[game][dest])

            elif msg[1] == "ROOM":
                if msg[2] == "REMOVE":
                    self.rooms.remove_room(game, dest)
                    self.room_frames[game].destroy()
                    self.room_frames[game] = None
                elif msg[2] == "START":
                    self.withdraw()
                    if game == "CHESS":
                        self.game = Chess(
                            msg[3], lambda move: self.send((dest, "MSG", move))
                        )
            elif msg[1] == "MSG":
                if game == "CHESS":
                    self.game.opp_move(msg[2])

    def send(self, msg):
        time_gap = 0.1
        new_time = time.perf_counter()
        if (self.sent_time + time_gap) > new_time:
            t = threading.Thread(
                target=self.queue_send,
                args=(msg, (self.sent_time + time_gap - new_time)),
            )
            t.start()
        else:
            self.queue_send(msg, None)

    def queue_send(self, msg, t):
        if t != None:
            self.sent_time = self.sent_time + 0.1
            time.sleep(t)
        else:
            self.sent_time = time.perf_counter() + 0.1
        print("Sent:", msg)
        self.cobj.send(msg)

    def start_arcade(self):
        self.http = Http("http://167.71.231.52:5000")
        self.login = Login(self, self.http, self.initialize)
        self.login.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        root.withdraw()

    def join_create(self, game):
        button_style = ttk.Style()
        button_style.configure("my.TButton", font=("times", 20))
        parent = self.chess_frame if game == "CHESS" else self.monopoly_frame

        join_button = ttk.Button(
            parent,
            text="Join A Room",
            style="my.TButton",
            command=lambda: self.join_lobby(game),
        )
        join_button.place(relx=0.5, rely=0.4, anchor="center")

        create_button = ttk.Button(
            parent,
            text="Create A Room",
            style="my.TButton",
            command=lambda: self.create_room(game),
        )
        create_button.place(relx=0.5, rely=0.6, anchor="center")

    def join_lobby(self, game):

        parent = self.chess_frame if game == "CHESS" else self.monopoly_frame
        self.lobby_frames[game] = tk.Frame(
            parent,
            width=self.screen_width / 3,
            height=self.screen_height / 1.1,
        )
        self.lobby_frames[game].place(relx=0.5, rely=0.5, anchor="center")
        frame = self.lobby_frames[game]

        tk.Button(
            frame,
            text="← BACK",
            font=("times", 10),
            highlightthickness=0,
            border=0,
            command=lambda: self.leave_lobby(game),
        ).place(relx=0.01, rely=0.01, anchor="nw")

        self.bind("<Escape>", lambda a: self.leave_lobby(game))

        scroll = ttk.Scrollbar(frame, orient="vertical")
        scroll.place(relx=1, rely=0, anchor="ne", relheight=1)

        self.lobby_trees[game] = ttk.Treeview(
            frame,
            columns=("Room", "Host", "Players"),
            yscrollcommand=scroll.set,
        )
        tree = self.lobby_trees[game]
        tree.place(relx=0, rely=0.05, anchor="nw", relheight=0.9, relwidth=0.96)

        tk.Button(
            frame,
            text="Join",
            font=("times", 13),
            command=lambda: self.join_selected_room(game, tree.selection()),
        ).place(relx=0.96, rely=1, anchor="se")
        scroll.configure(command=tree.yview)
        tree.column(
            "#0",
            width=10,
        )
        tree.column(
            "Room",
            width=self.screen_width // 10,
            anchor="center",
            minwidth=self.screen_width // 10,
        )
        tree.column(
            "Host",
            width=self.screen_width // 10,
            anchor="center",
            minwidth=self.screen_width // 10,
        )
        tree.column(
            "Players",
            width=self.screen_width // 10,
            anchor="center",
            minwidth=self.screen_width // 10,
        )

        tree.heading("#0", text="")
        tree.heading("Room", text="Room No.", anchor="center")
        tree.heading("Host", text="Host", anchor="center")
        tree.heading("Players", text="No. of Players", anchor="center")

        self.send(("0", "JOIN", game.upper()))

    def update_lobby(self, game):
        for item in self.lobby_trees[game].get_children():
            self.lobby_trees[game].delete(item)

        for id, room in self.rooms[game].items():
            if len(room["members"]) >= room["settings"]["MAX_PLAYERS"]:
                continue
            hostname = room["members"][room["host"]]["name"]
            self.lobby_trees[game].insert(
                parent="",
                index="end",
                iid=id,
                text="",
                values=(id, hostname, len(room["members"])),
            )

    def leave_lobby(self, game, frame_preserve=False):
        if not frame_preserve:
            self.lobby_frames[game].destroy()
            self.lobby_frames[game] = None
        self.unbind("<Escape>")
        self.send(("0", "LEAVE", game.upper()))

    def join_selected_room(self, game, room):
        if len(room) != 1:
            return
        self.leave_lobby(game, frame_preserve=True)
        self.send((game, "JOIN", room[0]))

    def create_room(self, game):
        settings = {"INITAL_STATUS": "OPEN", "MAX_PLAYERS": 2 if game == "CHESS" else 4}
        # TODO: Select Settings
        self.send((game, "CREATE", settings))

    def join_room(self, game, room):
        if self.lobby_frames[game]:
            self.lobby_frames[game].destroy()
            self.lobby_frames[game] = None

        room = self.rooms[game][room]
        self.current_room = room["id"]
        parent = self.chess_frame if game == "CHESS" else self.monopoly_frame
        hostname = (
            "You" if self.me == room["host"] else room["members"][room["host"]]["name"]
        )

        self.room_frames[game] = tk.Frame(
            parent,
            width=self.screen_width // 3,
            height=self.screen_height // 1.1,
        )
        frame = self.room_frames[game]
        frame.place(relx=0.5, rely=0.5, anchor="center")

        # Back Button
        tk.Button(
            frame,
            text="← BACK",
            font=("times", 10),
            highlightthickness=0,
            border=0,
            command=lambda: self.leave_room(game, room["id"], delete=hostname == "You"),
        ).place(relx=0.01, rely=0.01, anchor="nw")

        self.bind(
            "<Escape>",
            lambda a: self.leave_room(game, room["id"], delete=hostname == "You"),
        )

        # Room ID
        tk.Label(
            frame,
            text=f"Room ID: {room['id']}",
            font=("times", 13),
            highlightthickness=0,
            border=0,
        ).place(relx=0.5, rely=0.05, anchor="center")

        # Host
        tk.Label(
            frame,
            text=f"Host: {hostname}",
            font=("times", 13),
            highlightthickness=0,
            border=0,
        ).place(relx=0.5, rely=0.1, anchor="center")

        self.room_members[game] = tk.Frame(
            frame,
            width=self.screen_width // 3,
            height=self.screen_height // (2.5 * 1.1),
        )
        self.room_members[game].place(relx=0.5, rely=0.4, anchor="center")

        tk.Label(
            frame,
            text=f"Settings",
            font=("times 13 underline"),
            highlightthickness=0,
            border=0,
        ).place(relx=0.5, rely=0.5, anchor="center")

        # print settings here
        if hostname == "You":
            tk.Button(
                frame,
                text="START",
                font=("times", 13),
                command=lambda: self.start_room(game, room["id"]),
            ).place(relx=0.5, rely=0.9, anchor="center")
        else:
            tk.Label(
                frame,
                text="Waiting for Host to start the game",
                font=("times", 13),
            ).place(relx=0.5, rely=0.9, anchor="center")

        self.update_room(game, room)

    def update_room(self, game, room):
        for child in self.room_members[game].winfo_children():
            child.destroy()
        tk.Label(
            self.room_members[game],
            text=f"Members",
            font=("times 13 underline"),
            highlightthickness=0,
            border=0,
        ).place(relx=0.5, rely=0.1, anchor="center")
        k = 2
        d = sorted(list(room["members"].values()), key=lambda x: x["name"])
        for i in d:
            tk.Label(
                self.room_members[game],
                text=i["name"],
                font=("times", 13),
                highlightthickness=0,
                border=0,
            ).place(relx=0.5, rely=(k / 10), anchor="center")
            k += 1

    def leave_room(self, game, room, delete=False):
        self.current_room = None
        self.room_frames[game].destroy()
        self.room_frames[game] = None
        self.send((room, "LEAVE"))
        if not delete:
            self.join_lobby(game)

    def start_room(self, game, room):
        self.send((room, "START"))


class Login(tk.Frame):
    def __init__(self, master, http, complete):
        super().__init__(master)
        tk.Label(self, text="Please enter details below to login").pack()
        tk.Label(self, text="").pack()
        self.uname = tk.StringVar()
        self.pwd = tk.StringVar()

        tk.Label(self, text="Username: ").pack()
        self.uentry = tk.Entry(self, textvariable=self.uname)
        self.uentry.pack()
        self.uentry.focus_set()
        tk.Label(self, text="").pack()
        tk.Label(self, text="Password * ").pack()
        self.pwdentry = tk.Entry(self, textvariable=self.pwd, show="*")
        self.pwdentry.pack()
        self.uentry.bind("<Return>", lambda a: self.pwdentry.focus_set())
        tk.Label(self, text="").pack()
        tk.Button(self, text="Login", width=10, height=1, command=self.login).pack()
        self.pwdentry.bind("<Return>", lambda a: self.login())

        self.notif = None
        self.notifc = 0
        self.http = http
        self.complete = complete

    def login(self):
        uname = self.uentry.get().strip()
        pwd = self.pwd.get().strip()
        self.pwdentry.delete(0, tk.END)
        msg = ""
        if not (uname and pwd):
            msg = "Enter Required Fields"
        elif self.http.login(uname, pwd):
            msg = "Success"
            self.complete(uname, self.http.TOKEN)
        else:
            msg = "Failure"
        self.prompt(msg)

    def prompt(self, msg):
        try:
            self.destroyprompt()
            self.notifc += 1
            color = "red"
            if msg == "Success":
                color = "green"
            self.notif = (
                tk.Label(self, text=msg, fg=color, font=("calibri", 11)),
                self.notifc,
            )
            self.notif[0].pack()
            self.after(3000, self.destroyprompt)
        except:
            pass

    def destroyprompt(self):
        if self.notif and self.notif[1] == self.notifc:
            self.notif[0].destroy()
            self.notif = None


if __name__ == "__main__":
    root = tk.Tk()
    arc = Arcade()
    arc.start_arcade()
    root.mainloop()
