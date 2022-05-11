# import modules

import tkinter as tk
from tkinter import ttk
from http_wrapper import Http
from client_framework import Client

users = {"Pramit": "123"}


class Gamestate:
    def __init__(self):
        self.channels = {}

    def connect(self, name="Pramit"):
        self.conn = Client(("localhost", 6891), self.updater)
        self.conn.send(name)

    def updater(self, instruction):
        if instruction[0] == 403:
            print("Auth Error")
            return

    def create_channel(self, channel_id):
        pass


class Login(tk.Toplevel):
    def __init__(self, http: Http, complete):
        super().__init__()
        self.title("Login")
        self.geometry("300x250")
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


class Games(tk.Toplevel):
    def __init__(self, updater):
        super().__init__()
        self.title("Login")
        self.geometry("1000x500")
        self.nb = ttk.Notebook(self)
        self.nb.pack(expand=True)
        self.updater = updater
        self.chess = Chess(self)
        self.chess1 = Chess(self)
        self.chess.pack()
        self.chess1.pack()
        self.nb.add(child=self.chess, text="Chess")
        self.nb.add(child=self.chess1, text="Chess1")


class Chess(tk.Frame):
    def __init__(self, master):
        super().__init__(master, height=400, width=400)
        self.coj = Create_Join(self, self.join, self.create)
        self.coj.pack()
        self.updater = master.updater

    def join(self):
        self.coj.destroy()
        self.lobby = Lobby(self, "CHESS")

    def create(self):
        self.coj.destroy()
        print("Create")


class Lobby(tk.Frame):
    def __init__(self, master, game) -> None:
        super().__init__(master)
        self.grid(sticky=tk.NSEW)
        self.frames = []
        self.rooms = []
        self.updatee = master.updater
        self.game = game
        self.initialise()

        self.updatee((self.game, "JOIN"))

    def initialise(self):

        for i in range(1, 16):
            self.grid_rowconfigure(i, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.label = tk.Label(self, text="Rooms Avaliable", font=("Sans", 10))
        self.label.grid(row=1, column=1, sticky=tk.NSEW, pady=2)
        self.label.grid_propagate(0)
        for i in range(2, 16):
            self.frames.append(None)

    def updater(self):
        for i in range(len(self.rooms)):
            room_id = self.rooms[i]["roomnum"]
            host = self.rooms[i]["host"]
            noply = len(self.rooms[i]["players"])
            f = tk.Frame(self, highlightbackground="BLACK", highlightthickness=2)
            f.grid(row=i + 2, column=1, sticky=tk.NSEW, pady=2)
            f.grid_columnconfigure(1, weight=1)
            f.grid_columnconfigure(2, weight=1)
            f.grid_columnconfigure(3, weight=1)
            f.grid_columnconfigure(4, weight=1)
            f.grid_columnconfigure(5, weight=1)
            f.grid_rowconfigure(1, weight=1)
            room = tk.Label(f, text=str(room_id))
            room.grid(column=1, row=1, sticky=tk.NSEW)
            host = tk.Label(f, text=host)
            host.grid(column=2, row=1, sticky=tk.NSEW)
            noply = tk.Label(f, text=noply)
            noply.grid(column=3, row=1, sticky=tk.NSEW)
            join = tk.Button(
                f,
                text="Join",
                command=lambda a=room_id: self.parent.join_room(a),
            )
            join.grid(column=5, row=1, sticky=tk.NSEW)
            self.frames[i] = f

        for i in range(len(self.rooms), len(self.frames)):
            if self.frames[i] != None:
                self.frames[i].destroy()
                self.frames[i] = None

    def addroom(self, rooms):
        for i in rooms:
            self.rooms.append(i)
        self.updater()

    def removeroom(self, room):
        for i in self.rooms:
            if i["roomnum"] == room:
                self.rooms.remove(i)
        self.updater()


class Create_Join(tk.Frame):
    def __init__(self, master, joinhandle, createhandle):
        super().__init__(master)
        self = tk.Frame(self, border=1)
        self.grid(sticky=tk.NSEW)
        self.grid_columnconfigure(1, weight=2)
        self.grid_columnconfigure(2, weight=2)
        self.grid_columnconfigure(3, weight=2)
        self.grid_columnconfigure(4, weight=2)
        self.grid_columnconfigure(5, weight=2)
        self.grid_rowconfigure(1, weight=4)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=4)
        text = tk.Label(
            self,
            text="Do you want to Create or Join a room",
            anchor=tk.CENTER,
            font=("Sans", 16),
        )
        text.grid(column=2, row=1, columnspan=3, sticky="nsew")
        create = tk.Button(
            self,
            text="Create",
            font=("Sans", 12),
            anchor=tk.CENTER,
            command=createhandle,
        )
        join = tk.Button(
            self,
            text="Join",
            font=("Sans", 12),
            anchor=tk.CENTER,
            command=joinhandle,
        )
        create.grid(column=2, row=2, sticky=tk.NSEW)
        join.grid(column=4, row=2, sticky=tk.NSEW)


class InRoom(tk.Frame):
    def __init__(self, master, host) -> None:
        super().__init__(master)
        self.host = host
        self.grid(sticky=tk.NSEW)
        self.players = []
        self.pframes = []
        self.initialise()

    def initialise(self):
        for i in range(1, 16):
            self.grid_rowconfigure(i, weight=1)

        self.grid_columnconfigure(1, weight=1)
        self.label = tk.Label(self, text="Players", font=("Sans", 10))
        self.label.grid(row=1, column=1, sticky=tk.NSEW, pady=2)
        for i in range(2, 15):
            self.pframes.append(None)
        if self.host == self.parent.id:
            self.start = tk.Button(
                self,
                text="Start",
                font=("Sans", 10),
                command=lambda: self.parent.updater(("START",)),
            )
            self.start.grid(row=15, column=1, sticky=tk.E)

    def updater(self):
        for i in range(len(self.players)):
            name = self.players[i]["name"]
            f = tk.Frame(self, highlightbackground="black", highlightthickness=2)
            f.grid(row=i + 2, column=1, sticky=tk.NSEW, pady=2)
            f.grid_columnconfigure(1, weight=1)
            f.grid_columnconfigure(2, weight=1)
            f.grid_columnconfigure(3, weight=1)
            f.grid_rowconfigure(1, weight=1)
            font = ("Helvetica", 7)
            playernum = tk.Label(f, text=str(i), font=font, anchor=tk.CENTER)
            playernum.grid(column=1, row=1, sticky=tk.NSEW)
            playername = tk.Label(f, text=name, font=font, anchor=tk.CENTER)
            playername.grid(column=2, row=1, sticky=tk.NSEW)
            playername.grid_propagate(0)
            self.pframes[i] = f

        for i in range(len(self.players), len(self.pframes) - 1):
            if self.pframes[i] != None:
                self.pframes[i].destroy()
                self.pframes[i] = None

    def addplayers(self, player):
        print(player)
        self.players.extend(player)
        self.updater()

    def removeplayers(self, player):
        for i in self.players:
            if i["puid"] == player:
                self.rooms.remove(i)
        self.updater()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.http = Http("https://localhost:5000/")
        # self.login = Login(http=self.http, complete=self.login_complete)
        self.games()

    def login_complete(self, name, session_id):
        self.login.destroy()
        self.session_id = session_id
        self.games()

    def games(self):
        self.games = Games(self.conn.send)


g = Gamestate()
root = App()
root.mainloop()
