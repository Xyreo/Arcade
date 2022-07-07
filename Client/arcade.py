import base64
import os
import random
import sys
import threading
import time
import tkinter as tk
import tkinter.ttk as ttk
from io import BytesIO
from tkinter import filedialog as fd
from tkinter import messagebox as msgb

from PIL import Image, ImageChops, ImageDraw, ImageTk
from plyer import notification as noti

from chess import Chess
from client_framework import Client
from http_wrapper import Http
from monopoly import Monopoly

ASSET = os.path.join("Assets", "Home_Assets")
ASSET = ASSET if os.path.exists(ASSET) else os.path.join("Client", ASSET)


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


ASSET = resource_path(ASSET)
HTTP = Http("http://167.71.231.52:5000")
CLIENT_ADDRESS = "167.71.231.52"
isWin = os.name == "nt"
REMEMBER_ME_FILE = (
    os.path.join(
        os.environ["USERPROFILE"],
        "AppData",
        "Local",
        "Arcade",
        "remember_login.txt",
    )
    if isWin
    else os.path.join(
        os.environ["HOME"],
        "Applications",
        "Arcade",
        "remember_login.txt",
    )
)

if not isWin:
    print("I don't like your Operating System. Install Windows.")


class Rooms(dict):
    def __init__(self):
        super().__init__({"CHESS": {}, "MNPLY": {}})

    def __contains__(self, val):
        if val in self["CHESS"] or val in self["MNPLY"]:
            return True
        return False

    def initialize(self, game, rooms):
        self[game] = {}
        for room in rooms:
            self.add_room(game, room)

    def add_room(self, game, room):
        room["members"] = {i["puid"]: i for i in room["members"]}
        self[game][room["id"]] = room

    def remove_room(self, game, id):
        del self[game][id]

    def change_settings(self, rid, settings):
        key = "CHESS" if rid in self["CHESS"] else "MNPLY"
        self[key][rid]["settings"].update(settings)

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
        self.protocol("WM_DELETE_WINDOW", self.exit)
        self.iconbitmap(os.path.join(ASSET, "icon.ico"))
        if isWin:
            self.thr = threading.Thread(target=self.CLI, daemon=True)
            self.thr.start()

        self.current_room = None

    # region # Initialising

    def initialize(self, name, token):
        self.geometry(
            f"{self.screen_width}x{self.screen_height}+{self.x_coord}+{self.y_coord}"
        )
        self.name = name
        self.token = token
        self.rooms = Rooms()

        self.current_room = None

        self.cobj = Client((CLIENT_ADDRESS, 6969), self.event_handler, token)
        self.cobj.send((self.name,))

        self.main_notebook = ttk.Notebook(self)
        self.main_notebook.place(relx=0, rely=0, anchor="nw", relheight=1, relwidth=1)

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

        Arcade.store_pfp(self.name)
        self.my_pfp = Arcade.get_cached_pfp(self.name, (40, 40))

        self.acc_button = tk.Button(
            self,
            image=self.my_pfp,
            text=f" {self.name} ▾",
            bg="white",
            highlightthickness=0,
            border=0,
            font=("times 14 bold"),
            compound="left",
            command=self.account_tab,
        )
        self.acc_button.place(relx=0.99, rely=0.07, anchor="e")
        self.acc_frame = tk.Frame()
        self.acc_frame.destroy()

    def start_arcade(self):
        root.withdraw()
        button_style = ttk.Style()
        button_style.configure("20.TButton", font=("times", 20))
        button_style.configure("15.TButton", font=("times", 15))
        button_style.configure("12.TButton", font=("times", 12))

        if os.path.exists(REMEMBER_ME_FILE):
            self.login = Login(self, self.initialize, remember_login=True)
        else:
            self.logo = ImageTk.PhotoImage(
                Image.open(os.path.join(ASSET, "Logo.png")).resize(
                    (self.screen_width // 4, self.screen_width // 4),
                    Image.Resampling.LANCZOS,
                )
            )
            a = tk.Frame(self)
            a.place(relx=0.5, rely=0.3, anchor="center", relheight=0.6, relwidth=1)
            tk.Label(a, image=self.logo).place(
                relx=0.5, rely=0.5, anchor="center", relheight=1
            )
            self.login = Login(self, self.initialize)
        self.login.place(relx=0.5, rely=0.6, relheight=0.4, relwidth=1, anchor="n")

    def join_create(self, game):
        parent = self.chess_frame if game == "CHESS" else self.monopoly_frame

        join_button = ttk.Button(
            parent,
            text="Join A Room",
            style="20.TButton",
            command=lambda: self.join_lobby(game),
        )
        join_button.place(relx=0.5, rely=0.4, anchor="center")

        create_button = ttk.Button(
            parent,
            text="Create A Room",
            style="20.TButton",
            command=lambda: self.create_room(game),
        )
        create_button.place(relx=0.5, rely=0.6, anchor="center")

    # endregion

    # region # Event Handling

    def event_handler(self, msg):
        dest = msg[0]
        print("Recv:", msg)
        room = None
        if dest == "NAME":
            self.me = msg[1]
        elif dest == "GAME":
            if msg[1] == "SESSION_EXP":
                pass  # TODO session expired stuff
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
            elif msg[1] == "SETTINGS":
                self.rooms.change_settings(msg[3], msg[2])
            self.update_lobby(dest)  # TODO Settings GUI in Lobby

        elif dest == "ROOM":
            self.rooms.add_room(msg[1], msg[2])
            self.join_room(msg[2]["id"], msg[1])

        elif dest == self.current_room:
            game = "CHESS" if dest in self.rooms["CHESS"] else "MNPLY"
            if msg[1] == "PLAYER":
                if msg[2] == "ADD":
                    self.rooms.add_player(dest, msg[3])
                elif msg[2] == "REMOVE":
                    self.rooms.remove_player(dest, msg[3])
                self.update_room(self.rooms[game][dest])

            elif msg[1] == "SETTINGS":
                self.rooms.change_settings(dest, msg[2])
                self.update_room(self.rooms[game][dest])  # TODO Settings GUI in Room

            elif msg[1] == "ROOM":
                self.room_frames[game].destroy()
                self.room_frames[game] = None
                if msg[2] == "REMOVE":
                    self.rooms.remove_room(game, dest)
                elif msg[2] == "START":
                    self.withdraw()
                    if game == "CHESS":
                        self.game = Chess(
                            msg[3],
                            lambda move: self.send((dest, "MSG", move)),
                            HTTP,
                            back=self.end_game,
                        )
                    elif game == "MNPLY":
                        details = msg[3]
                        self.game = Monopoly(
                            details[0],
                            details[1],
                            lambda msg: self.send((dest, *msg)),
                            HTTP,
                            details[2],
                            back=self.end_game,
                        )

            elif msg[1] == "MSG":
                self.game.event_handler(msg[2])

    def send(self, msg):
        time_gap = 0.1
        new_time = time.perf_counter()
        if (self.sent_time + time_gap) > new_time:
            t = threading.Thread(
                target=self.queue_send,
                args=(msg, (self.sent_time + time_gap - new_time)),
            )
            t.daemon = True
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

    # endregion

    # region # Account Tab

    def account_tab(self):
        if self.acc_frame.winfo_exists():
            self.unbind("<Button-1>")
            self.acc_frame.destroy()
        else:
            try:
                self.change_frame.destroy()
            except:
                pass

            def clicked(e):
                if self.acc_frame.winfo_containing(e.x_root, e.y_root) not in [
                    self.log_out_button,
                    self.change_pass_button,
                    self.change_pfp_button,
                    self.acc_frame,
                    self.acc_button,
                ]:
                    self.acc_frame.destroy()
                    self.unbind("<Button-1>")

            self.bind("<Button-1>", lambda e: clicked(e))
            self.acc_frame = tk.Frame(self)
            self.acc_frame.place(relx=0.99, rely=0.1, anchor="ne")

            self.log_out_button = ttk.Button(
                self.acc_frame, text="Log Out", style="12.TButton", command=self.log_out
            )
            self.log_out_button.grid(
                row=0,
                column=0,
                sticky="nsew",
            )

            self.change_pass_button = ttk.Button(
                self.acc_frame,
                text="Change Password",
                style="12.TButton",
                command=self.change_password,
            )
            self.change_pass_button.grid(row=1, column=0, sticky="nsew")

            self.change_pfp_button = ttk.Button(
                self.acc_frame,
                text="Change Picture",
                style="12.TButton",
                command=self.change_pfp,
            )
            self.change_pfp_button.grid(row=2, column=0, sticky="nsew")

    def change_password(self):
        self.acc_frame.destroy()
        self.change_frame = tk.Frame(self)
        self.change_frame.place(
            relx=0.99, rely=0.1, relheight=0.3, relwidth=0.25, anchor="ne"
        )
        self.pwd = tk.StringVar()
        self.confpwd = tk.StringVar()
        tk.Button(
            self.change_frame,
            text="← Cancel",
            font=("times", 11),
            highlightthickness=0,
            border=0,
            command=self.change_frame.destroy,
        ).place(relx=0.01, rely=0.01, anchor="nw")

        self.change_frame.bind("<Escape>", lambda a: self.change_frame.destroy())
        tk.Label(self.change_frame, text="New Password: ").place(
            relx=0.49, rely=0.25, anchor="e"
        )
        self.pwdentry = tk.Entry(self.change_frame, textvariable=self.pwd, show="*")
        self.pass_hidden = True
        self.pwdentry.place(relx=0.5, rely=0.25, relwidth=0.275, anchor="w")
        self.pwdentry.focus_set()
        tk.Label(self.change_frame, text="Confirm Password: ").place(
            relx=0.49, rely=0.4, anchor="e"
        )
        self.confpwdentry = tk.Entry(
            self.change_frame, textvariable=self.confpwd, show="*"
        )
        self.conf_pass_hidden = True
        self.confpwdentry.place(relx=0.5, rely=0.4, relwidth=0.275, anchor="w")

        self.pwdentry.bind("<Return>", lambda a: self.confpwdentry.focus_set())
        self.confpwdentry.bind("<Return>", lambda a: self.confpwdentry.focus_set())

        def chng_pass():
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
            missing = Register.check_pass(pwd)

            msg = ""
            if not pwd:
                self.pwdentry.delete(0, tk.END)
                msg = "Enter Password"
                prompt(msg)
            elif pwd and not confpwd:
                msg = "Confirm Password"
                prompt(msg)
            elif missing:
                self.pwdentry.delete(0, tk.END)
                msg = "Password should have:"
                for i in missing:
                    msg += "\n" + prompts[i]
                prompt(msg)
            elif confpwd != pwd:
                msg = "Password does not match"
                prompt(msg)
            else:
                if HTTP.change_password(pwd.strip()):
                    msg = "Confirming and Logging you out..."
                    prompt(msg)
                    self.after(2000, self.log_out())
                else:
                    self.pwdentry.delete(0, tk.END)
                    msg = "ERROR"
                    prompt(msg)

        def prompt(msg):
            try:
                destroyprompt()
                self.notifc += 1
                color = "red"
                if msg == "Confirming...":
                    color = "green"
                self.notif = (
                    tk.Label(
                        self.change_frame, text=msg, fg=color, font=("calibri", 11)
                    ),
                    self.notifc,
                )
                self.notif[0].place(
                    relx=0.5, rely=0.55 if "\n" not in msg else 0.7, anchor="center"
                )
                self.after(5000, destroyprompt)

            except:
                pass

        def destroyprompt():
            if self.notif and self.notif[1] == self.notifc:
                self.notif[0].destroy()
                self.notif = None

        self.change_button = ttk.Button(
            self.change_frame,
            text="CHANGE",
            style="15.TButton",
            command=chng_pass,
        )
        self.change_button.place(relx=0.5, rely=0.7, anchor="center")

        self.show_password = ImageTk.PhotoImage(
            Image.open(os.path.join(ASSET, "show_password.png")).resize(
                (20, 15), Image.Resampling.LANCZOS
            )
        )

        self.hide_password = ImageTk.PhotoImage(
            Image.open(os.path.join(ASSET, "hide_password.png")).resize(
                (20, 15), Image.Resampling.LANCZOS
            )
        )

        self.show_hide_pass = tk.Button(
            self.change_frame,
            image=self.show_password,
            highlightthickness=0,
            border=0,
            command=lambda: toggle_hide_password(False),
        )
        self.show_hide_conf_pass = tk.Button(
            self.change_frame,
            image=self.show_password,
            highlightthickness=0,
            border=0,
            command=lambda: toggle_hide_password(True),
        )
        self.show_hide_pass.place(relx=0.8, rely=0.25, anchor="w")
        self.show_hide_conf_pass.place(relx=0.8, rely=0.4, anchor="w")

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

        self.confpwdentry.bind("<Return>", lambda a: chng_pass())

        self.notif = None
        self.notifc = 0

    def change_pfp(self):
        self.acc_frame.destroy()
        self.pfp_path = os.path.join(ASSET, "cached_pfp", self.name + ".png")
        self.change_frame = tk.Frame(self)
        self.change_frame.place(
            relx=0.99, rely=0.1, relheight=0.3, relwidth=0.25, anchor="ne"
        )
        tk.Button(
            self.change_frame,
            text="← Cancel",
            font=("times", 11),
            highlightthickness=0,
            border=0,
            command=self.change_frame.destroy,
        ).place(relx=0.01, rely=0.01, anchor="nw")
        self.select_pfp()

    def select_pfp(self):
        self.pfp_image = ImageTk.PhotoImage(
            Arcade.circle_PIL_Image(Image.open(self.pfp_path), (100, 100))
        )
        tk.Label(self.change_frame, image=self.pfp_image).place(
            relx=0.5, rely=0.3, anchor="center"
        )
        self.remove_image = ImageTk.PhotoImage(
            Image.open(os.path.join(ASSET, "remove.png")).resize(
                (32, 32),
                Image.Resampling.LANCZOS,
            )
        )

        def choose():
            n = fd.askopenfilename(
                title="Choose a Profile Picture",
                initialdir=r"%userprofile%",
                filetypes=(("Image Files", "*.jpg *.png *.webp *.gif *.jpeg"),),
            )
            self.pfp_path = n if n else self.pfp_path
            self.select_pfp()

        def set_default():
            self.pfp_path = os.path.join(ASSET, "default_pfp.png")
            self.select_pfp()

        self.remove_button = tk.Button(
            self.change_frame,
            image=self.remove_image,
            border=0,
            highlightthickness=0,
            command=set_default,
        )
        if self.pfp_path == os.path.join(ASSET, "default_pfp.png"):
            self.remove_button.destroy()
        else:
            self.remove_button.place(relx=0.7, rely=0.45, anchor="center")

        self.choose_button = ttk.Button(
            self.change_frame,
            text="Upload Picture",
            style="15.TButton",
            command=choose,
        )
        self.choose_button.place(relx=0.5, rely=0.625, anchor="center")

        def confirm_change():
            HTTP.change_pfp(Arcade.pfp_send(self.pfp_path))
            self.change_frame.destroy()
            Arcade.store_pfp(self.name)
            self.my_pfp = Arcade.get_cached_pfp(self.name)
            self.acc_button.configure(image=self.my_pfp)

            if self.current_room:
                self.update_room(self.rooms.get_rooms()[self.current_room])
            # TODO Update Leaderboard/ All the other places pfp is seen

        self.confirm_button = ttk.Button(
            self.change_frame,
            text="Confirm",
            style="15.TButton",
            command=confirm_change,
        )

        if self.pfp_path == os.path.join(ASSET, "cached_pfp", self.name + ".png"):
            self.confirm_button.destroy()
        else:
            self.confirm_button.place(relx=0.5, rely=0.9, anchor="center")

    def log_out(self):
        self.send(("GAME", "LEAVE"))
        HTTP.logout()
        try:
            os.remove(REMEMBER_ME_FILE)
        except FileNotFoundError:
            pass
        self.main_notebook.destroy()
        self.acc_button.destroy()
        self.acc_frame.destroy()
        try:
            self.change_frame.destroy()
        except:
            pass

        self.screen_width = int(0.9 * self.winfo_screenwidth())
        self.screen_height = int(self.screen_width / 1.9)
        self.x_coord = self.winfo_screenwidth() // 2 - self.screen_width // 2
        self.y_coord = (self.winfo_screenheight() - 70) // 2 - self.screen_height // 2

        self.title("Arcade")
        self.geometry(
            f"{self.screen_width//2}x{self.screen_height}+{self.x_coord+self.screen_width//4}+{self.y_coord}"
        )
        self.config(bg="white")
        self.protocol("WM_DELETE_WINDOW", self.exit)

        self.logo = ImageTk.PhotoImage(
            Image.open(os.path.join(ASSET, "Logo.png")).resize(
                (self.screen_width // 4, self.screen_width // 4),
                Image.Resampling.LANCZOS,
            )
        )
        a = tk.Frame(self)
        a.place(relx=0.5, rely=0.3, anchor="center", relheight=0.6, relwidth=1)
        tk.Label(a, image=self.logo).place(
            relx=0.5, rely=0.5, anchor="center", relheight=1
        )
        self.login = Login(self, self.initialize)
        self.login.place(relx=0.5, rely=0.6, relheight=0.4, relwidth=1, anchor="n")

    # endregion

    # region # Profile Picture

    @staticmethod
    def pfp_send(path):
        im = Image.open(path)
        im = im.crop(
            (
                (im.size[0] - min(im.size)) // 2,
                (im.size[1] - min(im.size)) // 2,
                (im.size[0] + min(im.size)) // 2,
                (im.size[1] + min(im.size)) // 2,
            )
        ).resize((256, 256), Image.Resampling.LANCZOS)
        im.save(os.path.join(ASSET, "temp.png"), optimize=True)
        with open(os.path.join(ASSET, "temp.png"), "rb") as f:
            a = base64.b64encode(f.read()).decode("latin1")
        os.remove(os.path.join(ASSET, "temp.png"))
        return a

    @staticmethod
    def pfp_make(img):
        b = base64.b64decode(img.encode("latin1"))
        c = Image.open(BytesIO(b))
        return c

    @staticmethod
    def store_pfp(name):
        Arcade.circle_PIL_Image(Arcade.pfp_make(HTTP.fetch_pfp(name))).save(
            os.path.join(ASSET, "cached_pfp", name + ".png")
        )

    @staticmethod
    def get_cached_pfp(name, resize=(32, 32)):
        return ImageTk.PhotoImage(
            Image.open(os.path.join(ASSET, "cached_pfp", name + ".png")).resize(
                resize, Image.Resampling.LANCZOS
            )
        )

    @staticmethod
    def circle_PIL_Image(pil_img: Image.Image, resize=(256, 256)):
        im = pil_img.convert("RGBA")
        im = im.crop(
            (
                (im.size[0] - min(im.size)) // 2,
                (im.size[1] - min(im.size)) // 2,
                (im.size[0] + min(im.size)) // 2,
                (im.size[1] + min(im.size)) // 2,
            )
        ).resize(resize, Image.Resampling.LANCZOS)
        bigsize = (im.size[0] * 10, im.size[1] * 10)

        mask = Image.new("L", bigsize, 0)
        ImageDraw.Draw(mask).ellipse((0, 0) + bigsize, fill=255)
        mask = mask.resize(im.size, Image.Resampling.LANCZOS)
        mask = ImageChops.darker(
            mask,
            im.split()[-1],
        )
        im.putalpha(mask)

        a = im.resize(bigsize)
        ImageDraw.Draw(a).ellipse((0, 0) + (bigsize), outline=(0, 0, 0), width=15)
        a = a.resize(im.size, Image.Resampling.LANCZOS)
        im.paste(a)

        return im

    # endregion

    def show_message(self, title, message, type="info", timeout=0):
        self.mbwin = tk.Tk()
        self.mbwin.withdraw()
        try:
            if timeout:
                self.mbwin.after(timeout, self.mbwin.destroy)
            if type == "info":
                msgb.showinfo(title, message, master=self.mbwin)
            elif type == "warning":
                msgb.showwarning(title, message, master=self.mbwin)
            elif type == "error":
                msgb.showerror(title, message, master=self.mbwin)
            elif type == "okcancel":
                okcancel = msgb.askokcancel(title, message, master=self.mbwin)
                return okcancel
            elif type == "yesno":
                yesno = msgb.askyesno(title, message, master=self.mbwin)
                return yesno
        except:
            print("Error")

    # region # Lobby

    def join_lobby(self, game):
        parent = self.chess_frame if game == "CHESS" else self.monopoly_frame
        self.lobby_frames[game] = tk.Frame(parent)
        self.lobby_frames[game].place(
            relx=0.5, rely=0.5, anchor="center", relwidth=0.33, relheight=0.9
        )
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
            command=lambda: self.join_selected_room(tree.selection(), game),
        )
        self.join_select_room_button.place(relx=0.96, rely=1, anchor="se")

        scroll.configure(command=tree.yview)
        tree.column(
            "#0",
            width=10,
        )
        tree.bind("<Return>", lambda a: self.join_selected_room(tree.selection(), game))

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

    # endregion

    # region # Room

    def join_selected_room(self, room, game=None):
        if room in self.rooms:
            game = "CHESS" if room in self.rooms["CHESS"] else "MNPLY"
        if len(room) != 1:
            return
        if self.current_room:
            if self.show_message(
                "Room Already Joined!",
                "Do you want to leave the previous room and join here?",
                "yesno",
            ):
                self.leave_room(self.current_room, confirm=False)
            else:
                return

        self.leave_lobby(game, frame_preserve=True)
        self.send((game, "JOIN", room[0]))

    def create_room(self, game):
        settings = {}
        if self.current_room:
            if self.show_message(
                "Room Already Joined!",
                "Do you want to leave the previous room and create a new one?",
                "yesno",
            ):
                self.leave_room(self.current_room, confirm=False)
            else:
                return
        if game == "CHESS":
            settings = {
                "STATUS": "PUBLIC",
                "MAX_PLAYERS": 2,
                "TIME": 10,
                "HOST_SIDE": random.choice(("BLACK", "WHITE")),
                "ADD_TIME": 5,
            }
        if game == "MNPLY":
            settings = {
                "STATUS": "PUBLIC",
                "MAX_PLAYERS": 4,
            }  # ? Colour, Speed Game, Auctions
        self.send((game, "CREATE", settings))

    def join_room(self, room, game=None):
        if room in self.rooms:
            game = "CHESS" if room in self.rooms["CHESS"] else "MNPLY"

        if self.lobby_frames[game]:
            self.lobby_frames[game].destroy()
            self.lobby_frames[game] = None

        room = self.rooms[game][room]
        self.current_room = room["id"]
        parent = self.chess_frame if game == "CHESS" else self.monopoly_frame
        hostname = (
            "You" if self.me == room["host"] else room["members"][room["host"]]["name"]
        )

        self.room_frames[game] = tk.Frame(parent)
        frame = self.room_frames[game]
        frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.33, relheight=0.9)

        tk.Button(
            frame,
            text="← BACK",
            font=("times", 10),
            highlightthickness=0,
            border=0,
            command=lambda: self.leave_room(room["id"], game, delete=hostname == "You"),
        ).place(relx=0.01, rely=0.01, anchor="nw")

        self.bind(
            "<Escape>",
            lambda a: self.leave_room(room["id"], game, delete=hostname == "You"),
        )

        tk.Label(
            frame,
            text=f"Room ID: {room['id']}",
            font=("times", 13),
            highlightthickness=0,
            border=0,
        ).place(relx=0.5, rely=0.05, anchor="center")

        tk.Label(
            frame,
            text=f"Host: {hostname}",
            font=("times", 13),
            highlightthickness=0,
            border=0,
        ).place(relx=0.5, rely=0.1, anchor="center")

        self.room_members[game] = tk.Frame(frame)
        self.room_members[game].place(
            relx=0.5, rely=0.3, anchor="center", relwidth=1, relheight=0.25
        )

        tk.Label(
            frame,
            text=f"Settings",
            font=("times 13 underline"),
            highlightthickness=0,
            border=0,
        ).place(relx=0.5, rely=0.6, anchor="center")

        # TODO: Show/Select Settings
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

        self.update_room(room, game)

    def update_room(self, room, game=None):
        if room["id"] in self.rooms:
            game = "CHESS" if room["id"] in self.rooms["CHESS"] else "MNPLY"
        for child in self.room_members[game].winfo_children():
            child.destroy()
        tk.Label(
            self.room_members[game],
            text=f"Members",
            font=("times 13 underline"),
            highlightthickness=0,
            border=0,
        ).place(relx=0.5, rely=0, anchor="n")
        k = 1
        d = sorted(list(room["members"].values()), key=lambda x: x["name"])
        for i in d:
            if not os.path.isfile(
                os.path.join(ASSET, "cached_pfp", i["name"] + ".png")
            ):
                Arcade.store_pfp(i["name"])
            i.update({"pfp": Arcade.get_cached_pfp(i["name"], (32, 32))})
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
                image=i["pfp"],
                text="  " + i["name"],
                font=("times", 13),
                highlightthickness=0,
                border=0,
                compound="left",
            ).place(relx=0.4, rely=(k / 4), anchor="w")
            k += 1

    def leave_room(self, room, game=None, delete=False, confirm=True):
        if room in self.rooms:
            game = "CHESS" if room in self.rooms["CHESS"] else "MNPLY"
        if confirm:
            if not self.show_message(
                "Leaving room!",
                f"Do you want to leave the room? {'The Room will be deleted if you leave'if delete else ''}",
                "yesno",
            ):
                return
        self.current_room = None
        self.room_frames[game].destroy()
        self.room_frames[game] = None
        self.send((room, "LEAVE", "Quit"))
        if not delete:
            self.join_lobby(game)

    def start_room(self, game, room):
        self.send((room, "START"))

    # endregion

    def end_game(self):
        self.deiconify()
        self.current_room = None

    def exit(self):
        if self.current_room:
            if self.show_message(
                "In a Room!",
                "Do you want to leave the room and exit arcade?",
                "yesno",
            ):
                pass
            else:
                return
        HTTP.logout()
        root.quit()
        for file in os.scandir(os.path.join(ASSET, "cached_pfp")):
            os.remove(file.path)

    def CLI(self):
        while True:
            t = tuple(i for i in input().split())
            if t:
                if t[0] == "cs":
                    self.send(
                        (
                            self.current_room,
                            "SETTINGS",
                            {"STATUS": "PRIVATE" if t[1] == "p" else "PUBLIC"},
                        )
                    )

                else:
                    print("Die")
            else:
                print("Closed CLI Thread")
                break


class Login(tk.Frame):
    def __init__(self, master, complete, remember_login=False):
        super().__init__(master)
        self.notif = None
        self.notifc = 0
        self.complete = complete

        if remember_login:
            master.withdraw()
            with open(
                REMEMBER_ME_FILE,
                "r",
            ) as f:
                uname, pwd = eval(f.readlines()[-1])
                self.check_login = HTTP.login(uname, pwd, remember_login=True)
                if self.check_login == 1:
                    master.deiconify()
                    self.complete(uname, HTTP.TOKEN)
                elif self.check_login == -1:
                    pass
                else:
                    print("File has been corrupted")

        master.deiconify()
        tk.Label(
            self, text="Welcome to the Arcade!\nPlease Enter your Credentials to Login:"
        ).place(relx=0.5, rely=0.1, anchor="center")
        self.uname = tk.StringVar()
        self.pwd = tk.StringVar()

        tk.Label(self, text="Username: ").place(relx=0.44, rely=0.3, anchor="e")

        def no_special(e):
            if not any(i in ["'", '"', ";", " "] for i in e) and len(e) <= 32:
                return True
            else:
                return False

        self.uentry = ttk.Entry(
            self,
            textvariable=self.uname,
            validate="key",
            validatecommand=(
                self.register(lambda e: no_special(e)),
                "%P",
            ),
        )
        self.uentry.place(relx=0.45, rely=0.3, relwidth=0.2, anchor="w")
        self.uentry.focus_set()
        tk.Label(self, text="Password: ").place(relx=0.44, rely=0.4, anchor="e")
        self.pwdentry = ttk.Entry(self, textvariable=self.pwd, show="*")
        self.pass_hidden = True
        self.pwdentry.place(relx=0.45, rely=0.4, relwidth=0.2, anchor="w")
        self.uentry.bind("<Return>", lambda a: self.pwdentry.focus_set())

        self.login_button = ttk.Button(
            self,
            text="LOGIN",
            style="15.TButton",
            command=self.login,
        )
        self.login_button.place(relx=0.5, rely=0.8, anchor="center")

        def forget_reg():
            self.reg.destroy()

        def register():
            self.reg = Register(self, forget_reg)
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
            Image.open(os.path.join(ASSET, "show_password.png")).resize(
                (20, 15), Image.Resampling.LANCZOS
            )
        )

        self.hide_password = ImageTk.PhotoImage(
            Image.open(os.path.join(ASSET, "hide_password.png")).resize(
                (20, 15), Image.Resampling.LANCZOS
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
            self.check_login = HTTP.login(
                uname.strip(), pwd.strip(), remember_me=self.remember_me.get()
            )
            if self.check_login:
                if self.check_login != -1:
                    msg = "Logging in..."
                    self.prompt(msg)
                    if isinstance(self.check_login, str):
                        self.store_password(uname.strip(), self.check_login)
                    else:
                        self.delete_stored_login()
                    self.after(1000, lambda: self.complete(uname, HTTP.TOKEN))
                else:
                    msg = "User logged in on another device!"
                    self.prompt(msg)
            else:
                msg = "Incorrect Username or Password"
                self.prompt(msg)

    def delete_stored_login(self):
        pass

    def store_password(self, uname, pwd):
        with open(
            REMEMBER_ME_FILE,
            "w",
        ) as f:
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
    def __init__(self, master, complete):
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

        def no_special(e):
            if not any(i in ["'", '"', ";", " "] for i in e) and len(e) <= 32:
                return True
            else:
                return False

        self.uentry = ttk.Entry(
            self,
            textvariable=self.uname,
            validate="key",
            validatecommand=(
                self.register(lambda e: no_special(e)),
                "%P",
            ),
        )
        self.uentry.place(relx=0.25, rely=0.3, relwidth=0.2, anchor="w")
        self.uentry.focus_set()
        tk.Label(self, text="Create Password: ").place(relx=0.24, rely=0.4, anchor="e")
        self.pwdentry = ttk.Entry(self, textvariable=self.pwd, show="*")
        self.pass_hidden = True
        self.pwdentry.place(relx=0.25, rely=0.4, relwidth=0.2, anchor="w")
        tk.Label(self, text="Confirm Password: ").place(relx=0.24, rely=0.5, anchor="e")
        self.confpwdentry = ttk.Entry(self, textvariable=self.confpwd, show="*")
        self.conf_pass_hidden = True
        self.confpwdentry.place(relx=0.25, rely=0.5, relwidth=0.2, anchor="w")

        self.uentry.bind("<Return>", lambda a: self.pwdentry.focus_set())
        self.pwdentry.bind("<Return>", lambda a: self.confpwdentry.focus_set())

        self.reg_button = ttk.Button(
            self,
            text="REGISTER",
            style="15.TButton",
            command=self.reg_user,
        )
        self.reg_button.place(relx=0.5, rely=0.8, anchor="center")

        self.show_password = ImageTk.PhotoImage(
            Image.open(os.path.join(ASSET, "show_password.png")).resize(
                (20, 15), Image.Resampling.LANCZOS
            )
        )

        self.hide_password = ImageTk.PhotoImage(
            Image.open(os.path.join(ASSET, "hide_password.png")).resize(
                (20, 15), Image.Resampling.LANCZOS
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
        self.complete = complete
        self.pfp_path = os.path.join(ASSET, "default_pfp.png")
        self.pfp_select()

    def pfp_select(self):
        self.pfp_image = ImageTk.PhotoImage(
            Arcade.circle_PIL_Image(Image.open(self.pfp_path), (100, 100))
        )
        tk.Label(self, image=self.pfp_image).place(
            relx=0.75, rely=0.26, anchor="center"
        )
        self.remove_image = ImageTk.PhotoImage(
            Image.open(os.path.join(ASSET, "remove.png")).resize(
                (32, 32),
                Image.Resampling.LANCZOS,
            )
        )

        def choose():
            n = fd.askopenfilename(
                title="Choose a Profile Picture",
                initialdir=r"%userprofile%",
                filetypes=(("Image Files", "*.jpg *.png *.webp *.gif *.jpeg"),),
            )
            self.pfp_path = n if n else self.pfp_path
            self.pfp_select()

        def set_default():
            self.pfp_path = os.path.join(ASSET, "default_pfp.png")
            self.pfp_select()

        self.remove_button = tk.Button(
            self,
            image=self.remove_image,
            border=0,
            highlightthickness=0,
            command=set_default,
        )
        if self.pfp_path == os.path.join(ASSET, "default_pfp.png"):
            self.remove_button.destroy()
        else:
            self.remove_button.place(relx=0.85, rely=0.35, anchor="center")

        self.choose_button = ttk.Button(
            self,
            text="Upload Picture",
            style="15.TButton",
            command=choose,
        )
        self.choose_button.place(relx=0.75, rely=0.5, anchor="center")

    @staticmethod
    def check_pass(pwd):
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
        missing = Register.check_pass(pwd)

        msg = ""
        if uname in [
            "none",
        ]:
            self.uentry.delete(0, tk.END)
            msg = "Illegal Username!"
            self.prompt(msg)
        elif uname and not pwd:
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
            if HTTP.register(
                uname.strip(),
                pwd.strip(),
                Arcade.pfp_send(self.pfp_path),
            ):
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
    try:
        os.mkdir(os.path.join(ASSET, "cached_pfp"))
        os.mkdir(
            os.path.join(
                os.environ["USERPROFILE"],
                "AppData",
                "Local",
                "Arcade",
            )
            if os.name == "nt"
            else os.path.join(
                os.environ["HOME"],
                "Applications",
                "Arcade",
            )
        )
    except:
        pass
    arc = Arcade()
    arc.start_arcade()
    root.mainloop()
