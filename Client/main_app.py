import tkinter as tk
import tkinter.ttk as ttk
from time import sleep
from tkinter import messagebox as msgb
from client_framework import Client
from http_wrapper import Http

import mysql.connector as msc
from PIL import Image, ImageOps, ImageTk


class Gamestate:
    def __init__(self):
        self.room = None
        self.lobby = None
        self.lobby_handler = {}
        self.room_handler = {}
        self.create_room = {}

    def login(self, name):
        self.cobj = Client(("localhost", 6778), self.event_handler)
        self.cobj.send(("Pramit"))

    def event_handler(self, msg):
        dest = msg[0]
        print("Msg:", msg)
        if dest in ["CHESS", "MNPLY"]:
            if msg[1] == "INIT":
                print(msg[3][1])
                for i in msg[3][1]:
                    self.lobby_handler[dest]["add"](i)
            elif msg[1] == "ROOM":
                if msg[2] == "ADD":
                    self.lobby_handler[dest]["add"](msg[3])
                    print("hmmm")
                elif msg[2] == "DELETE":
                    self.lobby_handler[dest]["delete"](msg[3])
        elif msg[1] == "INIT":
            self.room = dest
            g.create_room[msg[2]](dest)
            for i in msg[3]["members"]:
                g.room_handler[dest]["add"](i)

        elif dest == self.room:
            if msg[1] == "PLAYER":
                if msg[2] == "ADD":
                    g.room_handler[dest]["add"](msg[3])
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


g = Gamestate()


class Arcade(tk.Toplevel):
    def __init__(self):
        super().__init__()
        g.login("Pramit")
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
        self.screen_height = int(self.winfo_screenheight() * 0.8)
        g.width = self.screen_width
        g.height = self.screen_height

        self.title("Arcade")
        self.geometry(f"{self.screen_width}x{self.screen_height}")
        self.config(bg="white")
        self.protocol("WM_DELETE_WINDOW", root.destroy)
        self.withdraw()

    def start_arcade(self):
        self.deiconify()
        root.withdraw()

    def notebook(self):
        self.main_notebook = ttk.Notebook(
            self,
            height=int(self.screen_height * 0.95),
            width=int(self.screen_width * 0.95),
        )
        self.main_notebook.place(relx=0, rely=0, anchor="nw")

    def chess_tab(self):
        # self.chess_frame = tk.Frame(self.main_notebook, background="white")
        self.chess_frame = Tab(self.main_notebook, "CHESS")
        self.chess_frame.place(relx=0, rely=0, relheight=1, relwidth=1, anchor="nw")
        self.main_notebook.add(self.chess_frame, text="Chess")

    def monopoly_tab(self):
        # self.monopoly_frame = tk.Frame(self.main_notebook, background="white")
        self.monopoly_frame = Tab(self.main_notebook, "MNPLY")
        self.monopoly_frame.place(relx=0, rely=0, relheight=1, relwidth=1, anchor="nw")
        self.main_notebook.add(self.monopoly_frame, text="Monopoly")

    def join_selected_room(self, room):
        print("Joining", room)

    def create_room(self, parent, game):
        print("Creating", game)

    def event_handler(self, event):
        pass

    def send(self, msg):
        self.cobj.send(msg)


class Login(tk.Frame):
    def __init__(self, http, complete):
        super().__init__()
        tk.Label(self, text="Please enter details below to login").pack()
        tk.Label(self, text="").pack()
        self.uname = tk.StringVar()
        self.pwd = tk.StringVar()

        tk.Label(self, text="Username * ").pack()
        self.uentry = tk.Entry(self, textvariable=self.uname)
        self.uentry.pack()
        tk.Label(self, text="").pack()
        tk.Label(self, text="Password * ").pack()
        self.pwdentry = tk.Entry(self, textvariable=self.pwd, show="*")
        self.pwdentry.pack()
        tk.Label(self, text="").pack()
        tk.Button(self, text="Login", width=10, height=1, command=self.login).pack()

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
            self.notif = (
                tk.Label(self, text=msg, fg="green", font=("calibri", 11)),
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


class Tab(tk.Frame):
    def __init__(self, master, game):
        super().__init__(master)
        self.master = master
        self.game = game

        button_style = ttk.Style()
        button_style.configure("my.TButton", font=("times", 20))

        self.join_button = ttk.Button(
            self,
            text="Join A Room",
            style="my.TButton",
            command=lambda: self.join_lobby(game),
        )
        self.join_button.place(relx=0.5, rely=0.4, anchor="center")

        self.create_button = ttk.Button(
            self,
            text="Create A Room",
            style="my.TButton",
            command=lambda: self.create_room(game),
        )
        self.create_button.place(relx=0.5, rely=0.6, anchor="center")

        g.create_room[game] = self.room

    def join_lobby(self, game):
        self.join_frame = tk.Frame(
            self,
            width=g.width / 3,
            height=g.height / 1.1,
        )
        self.join_frame.place(relx=0.5, rely=0.5, anchor="center")
        self.bind("<Escape>", lambda a: self.quit_lobby())

        tk.Button(
            self.join_frame,
            text="← BACK",
            font=("times", 10),
            highlightthickness=0,
            border=0,
            command=self.quit_lobby,
        ).place(relx=0.01, rely=0.01, anchor="nw")

        tk.Button(
            self.join_frame,
            text="Join",
            font=("times", 13),
            command=lambda: g.send((game, "JOIN", self.lobby_tree.selection()[0])),
        ).place(relx=0.96, rely=1, anchor="se")

        scroll = ttk.Scrollbar(self.join_frame, orient="vertical")
        scroll.place(relx=1, rely=0, anchor="ne", relheight=1)

        self.lobby_tree = Lobby(self.join_frame, scroll.set, game)
        g.lobby_handler[game] = {}
        g.lobby_handler[game]["add"] = self.lobby_tree.add_room
        g.lobby_handler[game]["delete"] = self.lobby_tree.remove_room
        g.lobby_handler[game]["add"](
            {"id": 123, "host": 123, "members": [1, 2, 3], "settings": [12]}
        )
        self.lobby_tree.place(
            relx=0, rely=0.05, anchor="nw", relheight=0.9, relwidth=0.96
        )

        g.join_lobby(game)
        print(g.lobby_handler)
        scroll.configure(command=self.lobby_tree.yview)

    def quit_lobby(self):
        self.join_frame.place_forget()
        g.leave_lobby(self.game)

    def create_room(self, game):
        g.send((game, "CREATE", {}))

    def room(self, id):
        self.room_frame = tk.Frame(
            self,
            width=g.width / 3,
            height=g.height / 1.1,
        )
        self.room_frame.place(relx=0.5, rely=0.5, anchor="center")
        self.bind("<Escape>", lambda a: self.quit)

        tk.Button(
            self.room_frame,
            text="← BACK",
            font=("times", 10),
            highlightthickness=0,
            border=0,
            command=self.quit_room,
        ).place(relx=0.01, rely=0.01, anchor="nw")

        tk.Button(
            self.room_frame,
            text="Start",
            font=("times", 13),
            command=g.start_room,
        ).place(relx=0.96, rely=1, anchor="se")

        self.room_tree = Room(self.room_frame, id)
        g.room_handler[id] = {}
        g.room_handler[id]["add"] = self.room_tree.add_player
        g.room_handler[id]["delete"] = self.room_tree.remove_player

        self.room_tree.place(
            relx=0, rely=0.05, anchor="nw", relheight=0.9, relwidth=0.96
        )

    def quit_room(self):
        self.room_frame.destroy()


class Lobby(ttk.Treeview):  # JOIN
    def __init__(self, master, scroll, game):
        super().__init__(master, columns=("Room", "Host", "Players"), yscroll=scroll)
        self.game = game

        self.column("#0", width=10)
        width = g.width // 10
        self.column("Room", width=width, anchor="center", minwidth=width)
        self.column("Host", width=width, anchor="center", minwidth=width)
        self.column("Players", width=width, anchor="center", minwidth=width)

        self.heading("#0", text="")
        self.heading("Room", text="Room No.", anchor="center")
        self.heading("Host", text="Host", anchor="center")
        self.heading("Players", text="No. of Players", anchor="center")

    def add_room(self, room):
        id = room["id"]
        host = room["host"]
        nply = len(room["members"])
        settings = room["settings"]
        self.insert(
            parent="", index="end", iid=id, text="", values=(str(id)[:4], host, nply)
        )

    def remove_room(self, room):
        self.delete(room)


class Room(ttk.Treeview):  # Create
    def __init__(self, master, game):
        super().__init__(master, columns=("Player", "Name"))
        self.game = game

        self.column("#0", width=0)
        width = g.width // 10
        self.column("Player", width=width, anchor="center", minwidth=width)
        self.column("Name", width=width, anchor="center", minwidth=width)

        self.heading("#0", text="")
        self.heading("Name", text="Name", anchor="center")
        self.heading("Player", text="Player", anchor="center")

    def add_player(self, player):
        name = player["name"]
        id = player["puid"]
        self.insert(parent="", index="end", iid=id, text="", values=(id[:4], name))

    def remove_player(self, player):
        self.delete(player)


if __name__ == "__main__":
    root = tk.Tk()
    arc = Arcade()
    arc.start_arcade()
    root.mainloop()

"""self.rooms_tree.insert(
                    parent="",
                    index="end",
                    iid=i,
                    text="",
                    values=(i, j["Host"], j["Players"]),
                )"""


(
    "101d51d9ecc1256c5cf71edcbf75618e",
    "INIT",
    "CHESS",
    {
        "id": "101d51d9ecc1256c5cf71edcbf75618e",
        "host": "5abdf756a4142bfc98fb3ec284951e8e",
        "settings": {},
        "members": [
            {"name": "Pramit", "puid": "5abdf756a4142bfc98fb3ec284951e8e"},
            {"name": "Pramit", "puid": "4ab0caea05667a6fa5fddd4dad30bf3b"},
        ],
    },
)
(
    "101d51d9ecc1256c5cf71edcbf75618e",
    "PLAYER",
    "ADD",
    {"name": "Pramit", "puid": "4ab0caea05667a6fa5fddd4dad30bf3b"},
)
