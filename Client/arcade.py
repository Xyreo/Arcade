import json
import os
import threading
import time
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox as msgb

from PIL import Image, ImageOps, ImageTk

from chess import Chess
from client_framework import Client
from http_wrapper import Http
from monopoly import Monopoly

# TODO Confirmation Popups

ASSET = "Assets/Home_Assets"
ASSET = ASSET if os.path.exists(ASSET) else "Client/" + ASSET
HTTP = Http("http://167.71.231.52:5000")
CLIENT_ADDRESS = "167.71.231.52"


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

        # GUI Initializing
        self.screen_width = int(0.9 * self.winfo_screenwidth())
        self.screen_height = int(self.screen_width / 1.9)
        self.x_coord = self.winfo_screenwidth() // 2 - self.screen_width // 2
        self.y_coord = (self.winfo_screenheight() - 70) // 2 - self.screen_height // 2

        self.title("Arcade")
        self.geometry(
            f"{self.screen_width//2}x{self.screen_height}+{self.x_coord+self.screen_width//4}+{self.y_coord}"
        )
        self.config(bg="white")
        self.protocol("WM_DELETE_WINDOW", root.destroy)

    def initialize(self, name, token):
        # self.login.destroy()
        self.geometry(
            f"{self.screen_width}x{self.screen_height}+{self.x_coord}+{self.y_coord}"
        )
        self.name = name
        self.token = token
        self.rooms = Rooms()

        self.current_room = None

        self.cobj = Client((CLIENT_ADDRESS, 6969), self.event_handler)
        self.cobj.send((self.name))

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
                    elif game == "MNPLY":
                        det = msg[3]
                        self.game = Monopoly(
                            det[0],
                            det[1],
                            lambda msg: self.send((dest, "MSG", msg)),
                            HTTP,
                        )

            elif msg[1] == "MSG":
                if game == "CHESS":
                    self.game.opp_move(msg[2])

                if game == "MNPLY":
                    self.game.event_handler(msg[2])

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

    def show_message(self, title, message, type="info", timeout=0):
        mbwin = tk.Tk()
        mbwin.withdraw()
        try:
            if timeout:
                mbwin.after(timeout, mbwin.destroy)
            if type == "info":
                msgb.showinfo(title, message, master=mbwin)
            elif type == "warning":
                msgb.showwarning(title, message, master=mbwin)
            elif type == "error":
                msgb.showerror(title, message, master=mbwin)
            elif type == "okcancel":
                okcancel = msgb.askokcancel(title, message, master=mbwin)
                return okcancel
            elif type == "yesno":
                yesno = msgb.askyesno(title, message, master=mbwin)
                return yesno
        except:
            print("Error")

    def start_arcade(self):
        root.withdraw()

        # TODO: Add Logo, Terms of Use, Credits, date, time, (Greeting)
        if os.path.exists(ASSET + "/remember_login.txt"):
            self.login = Login(self, HTTP, self.initialize, remember_login=True)
        else:
            self.login = Login(self, HTTP, self.initialize)
        self.login.place(relx=0.5, rely=0.6, relheight=0.4, relwidth=1, anchor="n")

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

        self.join_select_room_button = tk.Button(
            frame,
            text="Join",
            font=("times", 13),
            command=lambda: self.join_selected_room(game, tree.selection()),
        )
        self.join_select_room_button.place(relx=0.96, rely=1, anchor="se")

        scroll.configure(command=tree.yview)
        tree.column(
            "#0",
            width=10,
        )
        tree.bind("<Return>", lambda a: self.join_selected_room(game, tree.selection()))

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
        if self.rooms[game]:
            self.join_select_room_button.configure(state="normal")
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
        else:
            self.join_select_room_button.configure(state="disabled")

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
            self.room_start_button = tk.Button(
                frame,
                text="START",
                font=("times", 13),
                command=lambda: self.start_room(game, room["id"]),
                state="disabled",
            )
            self.room_start_button.place(relx=0.5, rely=0.9, anchor="center")
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
        try:
            if len(d) > 1:
                self.room_start_button.configure(state="normal")
            else:
                self.room_start_button.configure(state="disabled")
        except:
            pass
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
    def __init__(self, master, http, complete, remember_login=False):
        super().__init__(master)
        self.notif = None
        self.notifc = 0
        self.http = http
        self.complete = complete

        if remember_login:
            master.withdraw()
            with open(ASSET + "/remember_login.txt", "r") as f:
                uname, pwd = eval(f.readlines()[-1])
                # TODO: Change to Frame
                if Arcade.show_message(
                    self,
                    "Login to Arcade?",
                    f"Do you wish to login as '{uname}'?",
                    type="yesno",
                ):
                    if self.http.login(uname, pwd, remember_login=True):
                        master.deiconify()
                        self.complete(uname, self.http.TOKEN)
                    else:
                        print("File has been corrupted")

        master.deiconify()
        tk.Label(
            self, text="Welcome to the Arcade!\nPlease Enter your Credentials to Login:"
        ).place(relx=0.5, rely=0.1, anchor="center")
        self.uname = tk.StringVar()
        self.pwd = tk.StringVar()

        tk.Label(self, text="Username: ").place(relx=0.44, rely=0.3, anchor="e")
        self.uentry = tk.Entry(self, textvariable=self.uname)
        self.uentry.place(relx=0.45, rely=0.3, relwidth=0.2, anchor="w")
        self.uentry.focus_set()
        tk.Label(self, text="Password: ").place(relx=0.44, rely=0.4, anchor="e")
        self.pwdentry = tk.Entry(self, textvariable=self.pwd, show="*")
        self.pass_hidden = True
        self.pwdentry.place(relx=0.45, rely=0.4, relwidth=0.2, anchor="w")
        self.uentry.bind("<Return>", lambda a: self.pwdentry.focus_set())

        button_style = ttk.Style()
        button_style.configure("small.TButton", font=("times", 15))

        self.login_button = ttk.Button(
            self,
            text="LOGIN",
            style="small.TButton",
            command=self.login,
        )
        self.login_button.place(relx=0.5, rely=0.8, anchor="center")

        def forget_reg():
            self.reg.destroy()

        def register():
            self.reg = Register(self, HTTP, forget_reg)
            self.reg.place(relx=0.5, rely=0.5, relheight=1, relwidth=1, anchor="center")

        tk.Button(
            self,
            text="New User? Click Here To Sign Up",
            font=("times", 11),
            fg="blue",
            highlightthickness=0,
            border=0,
            command=lambda: register(),
        ).place(relx=0.5, rely=0.6, anchor="center")

        self.show_password = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open(ASSET + "/show_password.png").resize(
                    (20, 15), Image.Resampling.LANCZOS
                )
            )
        )

        self.hide_password = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open(ASSET + "/hide_password.png").resize(
                    (20, 15), Image.Resampling.LANCZOS
                )
            )
        )

        self.show_hide_pass = tk.Button(
            self,
            image=self.show_password,
            highlightthickness=0,
            border=0,
            command=lambda: toggle_hide_password(),
        )
        self.show_hide_pass.place(relx=0.66, rely=0.4, anchor="w")
        self.remember_me = tk.BooleanVar()
        remember_me_button = ttk.Checkbutton(
            self,
            text="Remember Me",
            variable=self.remember_me,
            offvalue=False,
            onvalue=True,
        )
        remember_me_button.place(relx=0.45, rely=0.5, anchor="w")

        def toggle_hide_password():
            if self.pass_hidden:
                self.pwdentry.config(show="")
                self.show_hide_pass.config(image=self.hide_password)
            else:
                self.pwdentry.config(show="*")
                self.show_hide_pass.config(image=self.show_password)

            self.pass_hidden = not self.pass_hidden

        self.pwdentry.bind("<Return>", lambda a: self.login())

    def login(self):
        uname = self.uentry.get().strip()
        pwd = self.pwd.get().strip()
        self.pwdentry.delete(0, tk.END)
        msg = ""
        if uname and not pwd:
            msg = "Enter Password"
            self.prompt(msg)
        elif not uname:
            msg = "Enter your Credentials"
            pwd = ""
            self.prompt(msg)
        else:
            self.hashed_pass = self.http.login(
                uname.strip(), pwd.strip(), remember_me=self.remember_me.get()
            )
            if self.hashed_pass:
                msg = "Logging in..."
                self.prompt(msg)
                if isinstance(self.hashed_pass, str):
                    self.store_password(uname.strip(), self.hashed_pass)
                else:
                    self.delete_stored_login()
                self.after(1000, lambda: self.complete(uname, self.http.TOKEN))
            else:
                msg = "Incorrect Username or Password"
                self.prompt(msg)

    def delete_stored_login(self):
        pass

    def store_password(self, uname, pwd):
        with open(ASSET + "/remember_login.txt", "w") as f:
            f.write(
                f"WARNING!\nDo NOT Alter, Rename or Delete the contents of this file!\nThis File is required to remember Your Login Details\n\n{(uname,pwd)}"
            )

    def prompt(self, msg):
        try:
            self.destroyprompt()
            self.notifc += 1
            color = "red"
            if msg == "Logging in...":
                color = "green"
            self.notif = (
                tk.Label(self, text=msg, fg=color, font=("calibri", 11)),
                self.notifc,
            )
            self.notif[0].place(relx=0.5, rely=0.69, anchor="center")
            self.after(3000, self.destroyprompt)
        except:
            pass

    def destroyprompt(self):
        if self.notif and self.notif[1] == self.notifc:
            self.notif[0].destroy()
            self.notif = None


class Register(tk.Frame):
    def __init__(self, master, http, complete):
        super().__init__(master)
        tk.Label(
            self,
            text="Welcome to the Arcade!\nPlease Enter your Details to Create an Account:",
        ).place(relx=0.5, rely=0.1, anchor="center")
        self.uname = tk.StringVar()
        self.pwd = tk.StringVar()
        self.confpwd = tk.StringVar()
        tk.Button(
            self,
            text="← Sign In",
            font=("times", 11),
            highlightthickness=0,
            border=0,
            command=self.destroy,
        ).place(relx=0.01, rely=0.01, anchor="nw")
        self.bind("<Escape>", lambda a: self.destroy())
        tk.Label(self, text="Create Username: ").place(relx=0.24, rely=0.3, anchor="e")
        self.uentry = tk.Entry(self, textvariable=self.uname)
        self.uentry.place(relx=0.25, rely=0.3, relwidth=0.2, anchor="w")
        self.uentry.focus_set()
        tk.Label(self, text="Create Password: ").place(relx=0.24, rely=0.4, anchor="e")
        self.pwdentry = tk.Entry(self, textvariable=self.pwd, show="*")
        self.pass_hidden = True
        self.pwdentry.place(relx=0.25, rely=0.4, relwidth=0.2, anchor="w")
        tk.Label(self, text="Confirm Password: ").place(relx=0.24, rely=0.5, anchor="e")
        self.confpwdentry = tk.Entry(self, textvariable=self.confpwd, show="*")
        self.conf_pass_hidden = True
        self.confpwdentry.place(relx=0.25, rely=0.5, relwidth=0.2, anchor="w")

        self.uentry.bind("<Return>", lambda a: self.pwdentry.focus_set())
        self.pwdentry.bind("<Return>", lambda a: self.confpwdentry.focus_set())

        button_style = ttk.Style()
        button_style.configure("my.TButton", font=("times", 15))

        self.reg_button = ttk.Button(
            self,
            text="REGISTER",
            style="my.TButton",
            command=self.reg_user,
        )
        self.reg_button.place(relx=0.5, rely=0.8, anchor="center")

        self.show_password = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open(ASSET + "/show_password.png").resize(
                    (20, 15), Image.Resampling.LANCZOS
                )
            )
        )

        self.hide_password = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open(ASSET + "/hide_password.png").resize(
                    (20, 15), Image.Resampling.LANCZOS
                )
            )
        )

        self.show_hide_pass = tk.Button(
            self,
            image=self.show_password,
            highlightthickness=0,
            border=0,
            command=lambda: toggle_hide_password(False),
        )
        self.show_hide_conf_pass = tk.Button(
            self,
            image=self.show_password,
            highlightthickness=0,
            border=0,
            command=lambda: toggle_hide_password(True),
        )
        self.show_hide_pass.place(relx=0.46, rely=0.4, anchor="w")
        self.show_hide_conf_pass.place(relx=0.46, rely=0.5, anchor="w")

        for i in self.winfo_children():
            i.bind("<Escape>", lambda a: self.destroy())

        def toggle_hide_password(conf):
            if conf:
                if self.conf_pass_hidden:
                    self.confpwdentry.config(show="")
                    self.show_hide_conf_pass.config(image=self.hide_password)
                else:
                    self.confpwdentry.config(show="*")
                    self.show_hide_conf_pass.config(image=self.show_password)
                self.conf_pass_hidden = not self.conf_pass_hidden
            else:
                if self.pass_hidden:
                    self.pwdentry.config(show="")
                    self.show_hide_pass.config(image=self.hide_password)
                else:
                    self.pwdentry.config(show="*")
                    self.show_hide_pass.config(image=self.show_password)
                self.pass_hidden = not self.pass_hidden

        self.confpwdentry.bind("<Return>", lambda a: self.reg_user())

        self.notif = None
        self.notifc = 0
        self.http = http
        self.complete = complete

    def check_pass(self, pwd):
        check = {
            "length": False,
            "upper": False,
            "lower": False,
            "char": False,
            "digit": False,
            "space": True,
        }
        if len(pwd) >= 8:
            check["length"] = True
        if any(i.isupper() for i in pwd):
            check["upper"] = True
        if any(i.islower() for i in pwd):
            check["lower"] = True
        if any(i.isdigit() for i in pwd):
            check["digit"] = True
        if any(not i.isalnum() for i in pwd):
            check["char"] = True
        if any(i.isspace() for i in pwd):
            check["space"] = False

        return [i for i, j in check.items() if not j]

    def reg_user(self):
        uname = self.uentry.get().strip()
        pwd = self.pwd.get().strip()
        confpwd = self.confpwd.get().strip()

        self.confpwdentry.delete(0, tk.END)
        prompts = {
            "length": "Atleast 8 Characters in Total",
            "upper": "1 Upper Case Letter",
            "lower": "1 Lower Case Letter",
            "char": "1 Special Character",
            "digit": "1 Digit",
            "space": "No Spaces",
        }
        missing = self.check_pass(pwd)

        msg = ""
        if uname and not pwd:
            self.pwdentry.delete(0, tk.END)
            msg = "Enter Password"
            self.prompt(msg)
        elif uname and pwd and not confpwd:
            msg = "Confirm Password"
            self.prompt(msg)
        elif not uname:
            msg = "Enter your Credentials"
            pwd = ""
            confpwd = ""
            self.pwdentry.delete(0, tk.END)
            self.prompt(msg)
        elif missing:
            self.pwdentry.delete(0, tk.END)
            msg = "Password should have:"
            for i in missing:
                msg += "\n" + prompts[i]
            self.prompt(msg)
        elif confpwd != pwd:
            msg = "Password does not match"
            self.prompt(msg)
        else:
            if self.http.register(uname.strip(), pwd.strip()):
                msg = "Registering..."
                self.prompt(msg)
                self.after(1000, self.complete)
            else:
                self.uentry.delete(0, tk.END)
                self.pwdentry.delete(0, tk.END)
                msg = "User Already Registered"
                self.prompt(msg)

    def prompt(self, msg):
        try:
            self.destroyprompt()
            self.notifc += 1
            color = "red"
            if msg == "Registering...":
                color = "green"
            self.notif = (
                tk.Label(self, text=msg, fg=color, font=("calibri", 11)),
                self.notifc,
            )
            self.notif[0].place(relx=0.25, rely=0.7, anchor="center")
            self.after(5000, self.destroyprompt)
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
