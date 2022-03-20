from client_framework import Client
import threading
import tkinter as tk
import chess_interface


class App:
    def __init__(self) -> None:
        self.conn: Client = Client(("167.71.231.52", 6789))
        self.conn.startrecv(self.recv)
        self.room_handler = Room(self.send)

    def recv(self, x):
        if x[0] == "ROOM":
            self.room_handler(x[1:])

    def send(self, msg):
        self.conn.send(msg)


class Room:
    def __init__(self, send) -> None:
        self.t = threading.Thread(target=self.start_gui, args=(self.client_events))
        self.t.start()
        self.send = send

    def start_gui(self):
        self.gui = GUI(self.client_events)
        self.gui.mainloop

    def server_events(self, instruction):
        if instruction[0] == "START":
            self.gui.lobby.destroy()
            pass
        elif instruction[0] == "ADD":
            self.gui.lobby.addroom(instruction[1])
        elif instruction[0] == "ADDROOM":
            self.gui.inroom.addplayers(instruction[1:])
        elif instruction[0] == "REMOVE":
            self.gui.lobby.removeroom(instruction[1])

    def client_events(self, info):

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


class GUI(tk.Tk):
    def __init__(self, app_interface):
        super().__init__()
        self.initialize()
        self.updater = app_interface
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
            self.inroom = InRoom(self)
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


class Lobby:
    def __init__(self, parent) -> None:
        self.parent = parent
        self.frame = tk.Frame(parent)
        self.frame.grid(sticky=tk.NSEW)
        self.initialise()
        self.rooms = []

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
            f = tk.Frame(self.wrame, bg="BLUE")
            f.grid(row=i, column=1, sticky=tk.NSEW, pady=2)
            f.grid_columnconfigure(1, weight=1)
            f.grid_columnconfigure(2, weight=1)
            f.grid_columnconfigure(3, weight=1)
            f.grid_columnconfigure(4, weight=1)
            f.grid_columnconfigure(5, weight=1)
            room = tk.Label(f, text=str(room_id))
            room.grid(column=1, sticky=tk.NSEW)
            host = tk.Label(f, text=host)
            host.grid(column=2, sticky=tk.NSEW)
            noply = tk.Label(f, text=noply)
            noply.grid(column=3, sticky=tk.NSEW)
            join = tk.Button(
                text="Join", command=lambda a=room_id: self.parent.updater(("JOIN", a))
            )
            join.grid(column=5, sticky=tk.NSEW)
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
    def __init__(self, parent) -> None:
        self.parent = parent
        self.frame = tk.Frame(parent)
        self.frame.grid(sticky=tk.NSEW)
        self.players = []
        self.pframes = []

    def initialise(self):
        for i in range(1, 16):
            self.frame.grid_rowconfigure(i, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)
        self.label = tk.Label(self.frame, text="Players", font=("Sans", 10))
        self.label.grid(row=1, column=1, sticky=tk.NSEW, pady=2)
        for i in range(2, 16):
            self.pframes.append(None)

    def update(self):
        for i in range(len(self.players)):
            name = self.players[i]["name"]
            f = tk.Frame(self.wrame, bg="BLUE")
            f.grid(row=i, column=1, sticky=tk.NSEW, pady=2)
            f.grid_columnconfigure(1, weight=1)
            f.grid_columnconfigure(2, weight=1)
            f.grid_columnconfigure(3, weight=1)
            playernum = tk.Label(f, text=str(i))
            playernum.grid(column=1, sticky=tk.NSEW)
            playername = tk.Label(f, text=name)
            playername.grid(column=2, sticky=tk.NSEW)
            self.pframes[i] = f

        for i in range(len(self.rooms), len(self.pframes) - 1):
            if self.pframes[i] != None:
                self.pframes[i].destroy()
                self.pframes[i] = None

    def addplayers(self, player):
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
