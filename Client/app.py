from client_framework import Client
import threading
import tkinter as tk
import chess_interface
from multiplayer_chess import Chess


class App:
    def __init__(self) -> None:
        self.conn: Client = Client(("167.71.231.52", 6789))
        self.room_handler = Room(self.send)
        self.conn.startrecv(self.recv)
        self.room_handler.start_gui()

    def recv(self, x):
        if x[0] == "ROOM":
            self.room_handler.server_events(x[1:])
        if x[0] == "CHESS":
            self.chess(x[1:])

    def send(self, msg):
        print("Beep Boop: ", msg)
        self.conn.send(msg)

    def chess(self, instruction):
        print("Chess", instruction)
        if instruction[0] == "START":
            self.chess_handler = chess_interface.ClientInterface(self.send)
            self.chesss = Chess(instruction[1], self.chess_handler.played)
        elif instruction[0] == "MOVE":
            self.chesss.move(multi=[True, instruction[1]])


class Room:
    def __init__(self, send) -> None:
        """self.t = threading.Thread(target=self.start_gui)
        self.t.start()"""
        self.send = send

    def start_gui(self):
        self.gui = GUI(self.client_events)
        self.gui.mainloop()
        print("Test")

    def server_events(self, instruction):
        print("Server sent:", instruction)
        if instruction[0] == "ADD":
            self.gui.lobby.addroom(instruction[1])
        elif instruction[0] == "ADDROOM":
            self.gui.inroom.addplayers(instruction[1])
        elif instruction[0] == "REMOVE":
            self.gui.lobby.removeroom(instruction[1])
        elif instruction[0] == "NAME":
            self.gui.id = instruction[1]

    def client_events(self, info):
        print("Client sent:", info)
        if info[0] == "CREATE":
            self.send(("ROOM", "CREATE", info[1]))

        elif info[0] == "NAME":
            self.send(("NAME", info[1]))

        elif info[0] == "JOIN":
            self.send(("ROOM", "JOIN", info[1]))

        elif info[0] == "LIST":
            self.send(("ROOM", "LIST"))

        elif info[0] == "START":
            self.send(("ROOM", "START"))

    def destroy(self):
        self.gui.destroy()


class GUI(tk.Tk):
    def __init__(self, app_interface):
        super().__init__()
        self.initialize()
        self.updater = app_interface
        self.id = None
        self.frames = []

    def initialize(self):
        height = self.winfo_screenheight() * 4 // 5
        width = self.winfo_screenwidth() * 4 // 5
        self.geometry(f"{width}x{height}")
        top = self.winfo_toplevel()
        top.rowconfigure(0, weight=1)
        top.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.starting_screen()

    def starting_screen(self):
        self.wframe = tk.Frame(self, border=1)
        self.wframe.grid(sticky=tk.NSEW)
        self.wframe.grid_columnconfigure(1, weight=2)
        self.wframe.grid_columnconfigure(2, weight=1)
        self.wframe.grid_columnconfigure(3, weight=2)
        self.wframe.grid_rowconfigure(1, weight=4)
        self.wframe.grid_rowconfigure(2, weight=1)
        self.wframe.grid_rowconfigure(3, weight=1)
        self.wframe.grid_rowconfigure(4, weight=4)
        wlabel = tk.Label(
            self.wframe,
            text="Welcome\nEnter your name to get started",
            font=("Helvetica", 16),
            anchor="center",
            height=7,
            width=15,
        )
        wlabel.grid_propagate(0)
        wlabel.grid(row=1, column=2, sticky=tk.NSEW)
        self.entry = tk.Entry(
            self.wframe, bd=2, width=3, font=("Sans", 16), justify=tk.CENTER
        )
        self.entry.grid(column=2, row=2, sticky=tk.NSEW)
        enter = tk.Button(
            self.wframe,
            command=self.submit_name,
            height=1,
            width=1,
            text="Enter",
            font=("Helvetica", 16),
        )
        enter.grid_propagate(0)
        enter.grid(column=2, row=3, sticky=tk.NSEW, padx=20, pady=50)

    def submit_name(self):
        s = self.entry.get()
        self.wframe.destroy()
        del self.wframe
        del self.entry
        self.updater(("NAME", s))
        self.create_or_join_gui()

    def create_or_join_handler(self, a):
        self.wframe.destroy()
        del self.wframe
        if a == "create":
            self.inroom = InRoom(self, self.id)
            self.updater(("CREATE", "CHESS"))
        else:
            self.lobby = Lobby(self)
            self.updater(("LIST",))

    def create_or_join_gui(self):
        self.wframe = tk.Frame(self, border=1)
        self.wframe.grid(sticky=tk.NSEW)
        self.wframe.grid_columnconfigure(1, weight=2)
        self.wframe.grid_columnconfigure(2, weight=2)
        self.wframe.grid_columnconfigure(3, weight=2)
        self.wframe.grid_columnconfigure(4, weight=2)
        self.wframe.grid_columnconfigure(5, weight=2)
        self.wframe.grid_rowconfigure(1, weight=4)
        self.wframe.grid_rowconfigure(2, weight=1)
        self.wframe.grid_rowconfigure(3, weight=4)
        text = tk.Label(
            self.wframe,
            text="Do you want to Create or Join a room",
            anchor=tk.CENTER,
            font=("Sans", 16),
        )
        text.grid(column=2, row=1, columnspan=3, sticky="nsew")
        create = tk.Button(
            self.wframe,
            text="Create",
            font=("Sans", 12),
            anchor=tk.CENTER,
            command=lambda: self.create_or_join_handler("create"),
        )
        join = tk.Button(
            self.wframe,
            text="Join",
            font=("Sans", 12),
            anchor=tk.CENTER,
            command=lambda: self.create_or_join_handler("join"),
        )
        create.grid(column=2, row=2, sticky=tk.NSEW)
        join.grid(column=4, row=2, sticky=tk.NSEW)

    def join_room(self, a):
        self.lobby.destroy()
        for i in self.lobby.rooms:
            if i["roomnum"] == a:
                self.inroom = InRoom(self, i["host"])
        self.updater(("JOIN", a))


class Lobby:
    def __init__(self, parent) -> None:
        self.parent: GUI = parent
        self.frame = tk.Frame(parent)
        self.frame.grid(sticky=tk.NSEW)
        self.frames = []
        self.rooms = []
        self.initialise()

    def initialise(self):
        for i in range(1, 16):
            self.frame.grid_rowconfigure(i, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)
        self.label = tk.Label(self.frame, text="Rooms Avaliable", font=("Sans", 10))
        self.label.grid(row=1, column=1, sticky=tk.NSEW, pady=2)
        self.label.grid_propagate(0)
        for i in range(2, 16):
            self.frames.append(None)

    def update(self):
        for i in range(len(self.rooms)):
            room_id = self.rooms[i]["roomnum"]
            host = self.rooms[i]["host"]
            noply = len(self.rooms[i]["players"])
            f = tk.Frame(self.frame, highlightbackground="BLACK", highlightthickness=2)
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
        self.update()

    def removeroom(self, room):
        for i in self.rooms:
            if i["roomnum"] == room:
                self.rooms.remove(i)
        self.update()

    def destroy(self):
        self.frame.destroy()


class InRoom:
    def __init__(self, parent, host) -> None:
        self.parent = parent
        self.host = host
        self.frame = tk.Frame(parent)
        self.frame.grid(sticky=tk.NSEW)
        self.players = []
        self.pframes = []
        self.initialise()

    def initialise(self):
        for i in range(1, 16):
            self.frame.grid_rowconfigure(i, weight=1)

        self.frame.grid_columnconfigure(1, weight=1)
        self.label = tk.Label(self.frame, text="Players", font=("Sans", 10))
        self.label.grid(row=1, column=1, sticky=tk.NSEW, pady=2)
        for i in range(2, 15):
            self.pframes.append(None)
        if self.host == self.parent.id:
            self.start = tk.Button(
                self.frame,
                text="Start",
                font=("Sans", 10),
                command=lambda: self.parent.updater(("START",)),
            )
            self.start.grid(row=15, column=1, sticky=tk.E)

    def update(self):
        for i in range(len(self.players)):
            name = self.players[i]["name"]
            f = tk.Frame(self.frame, highlightbackground="black", highlightthickness=2)
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
        self.update()

    def removeplayers(self, player):
        for i in self.players:
            if i["puid"] == player:
                self.rooms.remove(i)
        self.update()

    def destroy(self):
        self.frame.destroy()


if __name__ == "__main__":
    a: App = App()
    """g = GUI(print)
    g.mainloop()
"""
