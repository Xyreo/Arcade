import base64
import copy
import os
import pickle
import random
import sys
import threading
import tkinter as tk
import tkinter.ttk as ttk
from io import BytesIO
from time import sleep
from tkinter import messagebox as msgb

from PIL import Image, ImageChops, ImageDraw, ImageTk
from plyer import notification as noti

sys.path.append(os.path.join(os.path.abspath("."), "Client"))

from utils import theme
from utils.http_wrapper import Http
from utils.timer import Timer

try:
    from utils.musicplayer import play as music
except:
    print("No Output Devices Found")

ASSET = "assets"
ASSET = ASSET if os.path.exists(ASSET) else os.path.join("Client", ASSET)
HOME_ASSETS = os.path.join(ASSET, "home_assets")
MONOPOLY_ASSETS = os.path.join(ASSET, "mnply_assets")
SETTINGS_FILE = (
    os.path.join(
        os.environ["USERPROFILE"],
        "AppData",
        "Local",
        "Arcade",
        "settings.dat",
    )
    if os.name == "nt"
    else os.path.join(
        os.environ["HOME"],
        "Applications",
        "Arcade",
        "settings.dat",
    )
)
CURR_THEME = "dark"


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


ASSET = resource_path(ASSET)
HOME_ASSETS = resource_path(HOME_ASSETS)
MONOPOLY_ASSETS = resource_path(MONOPOLY_ASSETS)


class StoppableThread(threading.Thread):
    def __init__(self, func, alive_condition, sleep_time=0):
        super().__init__(target=self, daemon=True)
        self.alive = alive_condition
        self.func = func
        self.sleep_time = sleep_time

    def run(self):
        while self.alive:
            try:
                self.func()
            except tk.TclError as e:
                print("Tcl:", e)
            sleep(self.sleep_time)

    def stop(self):
        self.alive = False


class Property:
    def __init__(self, details):
        self.name = details[0]
        self.position = details[1]
        self.colour = details[2]
        self.hex = details[3]
        self.price = details[4]
        self.rent_values = [
            details[5],
            details[6],
            details[7],
            details[8],
            details[9],
            details[10],
            details[11],
        ]
        self.mortgage = details[12]
        self.build = details[13]

        self.owner = None
        self.houses = -1
        self.isMortgaged = False
        """
        No. of houses meaning:
        -1 : Rent
        0 : Rent with colour set
        1: Rent with 1 house
        2: Rent with 2 houses
        3: Rent with 3 houses
        4: Rent with 4 houses
        5: Rent with hotel
        """

    def rent(self, roll):
        if self.colour == "Station":
            return 25 * (2 ** (Property.game.count_colour(self.position) - 1))
        elif self.colour == "Utility":
            return roll * (
                Property.game.count_colour(self.position)
                * (Property.game.count_colour(self.position) + 3)
            )
        else:
            return self.rent_values[self.houses + 1]

    def value(self):
        val = self.price
        if 1 <= self.houses <= 5:
            val += self.houses * self.build

        return val


class Monopoly(tk.Toplevel):
    def __init__(self, playerdetails, me, send, hobj: Http, order=None, back=None):
        super().__init__()
        self.back_to_arcade = back
        self.player_details = dict(
            sorted(playerdetails.items(), key=lambda i: i[1]["Name"])
        )
        self.me = me
        self.chance = Chance(self, order[0])
        self.community = Community(self, order[1])
        Monopoly.http = hobj
        print(self.player_details[self.me])
        self.n = 0
        self.send_msg = lambda msg: send(("MSG", msg))
        self.send_leave = lambda reason: send(("LEAVE", reason))
        self.create_window()
        self.initialise()
        self.create_gui_divisions()
        self.create_image_obj()
        self.dice_tokens()
        self.action_frame_popup("Default")
        self.player_frame_popup()
        self.dead_player_details = {}

        for i in self.player_details:
            self.move(i, 0)

        if self.turn == self.me:
            self.bg_timer_thr = threading.Thread(
                target=self.timer_init,
                args=(
                    600,
                    lambda: self.player_leave(self.me, inactive=True),
                    "Inactivity Timer",
                ),
                daemon=True,
            )
            self.bg_timer_thr.start()

    def initialise(self):
        self.init_objects()
        self.properties = {}
        try:
            details = self.http.mply_details()
            for i in range(40):
                self.properties[i] = Property(details[i])
        except:
            print("Couldn't Access Property Details! Invalid Session.")
            exit()
        Property.game = self

        for i in self.player_details:
            if not os.path.isfile(
                os.path.join(
                    HOME_ASSETS, "cached_pfp", self.player_details[i]["Name"] + ".png"
                )
            ):
                Monopoly.store_pfp(self.player_details[i]["Name"])

            self.player_details[i].update(
                {
                    "Money": 1500,
                    "Injail": [False, 0],
                    "Position": 0,
                    "Properties": [],
                    "GOJF": 0,
                    "PLACES": {},
                    "PFP": Monopoly.get_cached_pfp(
                        self.player_details[i]["Name"], (32, 32)
                    ),
                }
            )  # Properties will store obj from properties dict

        if os.name == "nt":
            self.cli_thread = threading.Thread(target=self.CLI, daemon=True)
            self.cli_thread.start()

    def event_handler(self, msg):
        if msg[1] == "ROLL":
            self.roll_dice(msg[2], True)
        elif msg[1] == "BUY":
            self.buy_property(msg[2], msg[0], True)
        elif msg[1] == "BUILD":
            self.build_sell(*msg[2:5], True)
        elif msg[1] == "END":
            self.end_turn(True)
        elif msg[1] == "MORTGAGE":
            self.final_mortgage(msg[2], msg[3], True)
        elif msg[1] == "LEAVE":
            if msg[2] == "ENDED":
                pass
            elif msg[0] in self.uuids:
                self.player_leave(msg[0])
                self.post_leave(msg[0])
        elif msg[1] == "POLL":
            if self.me in self.uuids:
                self.poll(msg[0], msg[2], True)
            else:
                self.update_game("Players are deciding on ending the game!")
        elif msg[1] == "JAIL":
            self.out_of_jail(msg[2], True)
        elif msg[1] == "TRADE":
            if msg[2] == "ANSWER":
                if msg[3]:
                    self.exec_trade(msg[4], msg[0], *msg[5:8])
                else:
                    if msg[4] == self.me:
                        self.update_game("Your Trade Offer was declined!")
                if "TRADE" in self.collective:
                    del self.collective["TRADE"]
            elif msg[2] == "REQUEST":
                if msg[3] == self.me:
                    self.recv_trade(msg[0], *msg[4:7])
        elif msg[1] == "GAME_ENDED":
            self.end_game()

    # region # Profile Picture

    @staticmethod
    def pfp_make(img):
        b = base64.b64decode(img.encode("latin1"))
        c = Image.open(BytesIO(b))
        return c

    @staticmethod
    def store_pfp(name):
        Monopoly.circle_PIL_Image(
            Monopoly.pfp_make(Monopoly.http.fetch_pfp(name))
        ).save(os.path.join(HOME_ASSETS, "cached_pfp", name + ".png"))

    @staticmethod
    def get_cached_pfp(name, resize=(32, 32)):
        return ImageTk.PhotoImage(
            Image.open(os.path.join(HOME_ASSETS, "cached_pfp", name + ".png")).resize(
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

    # region # Create

    def init_objects(self):
        self.property_frame = tk.Frame()
        self.property_frame.destroy()
        self.end_button = ttk.Button()
        self.end_button.destroy()
        self.buy_button = ttk.Button()
        self.buy_button.destroy()
        self.build_button = ttk.Button()
        self.build_button.destroy()
        self.mortgage_button = ttk.Button()
        self.mortgage_button.destroy()
        self.unmortgage_button = ttk.Button()
        self.unmortgage_button.destroy()
        self.sell_button = ttk.Button()
        self.sell_button.destroy()
        self.trade_button = ttk.Button()
        self.trade_button.destroy()

        self.property_pos_displayed = None
        self.current_txt = "Default"

        self.uuids = list(self.player_details.keys())
        self.turn = self.uuids[0]
        self.doubles_counter = 0
        self.collective = {}

        self.isInDebt = False
        self.debt_details = []
        self.isEnding = False
        self.isEnded = False
        self.timer_display_thread = None
        self.timer: Timer = None

    def create_window(self):
        screen_width = int(0.9 * self.winfo_screenwidth())
        screen_height = int(screen_width / 1.9)
        x_coord = self.winfo_screenwidth() // 2 - screen_width // 2
        y_coord = (self.winfo_screenheight() - 70) // 2 - screen_height // 2

        self.board_side = int(screen_height * 0.9)  # Length of board
        self.property_width = self.board_side / 12.2  # Width of one property on board
        self.property_height = self.property_width * 1.6
        self.token_width = int(self.property_height * 0.176)

        self.title("Monopoly")
        self.iconbitmap(os.path.join(MONOPOLY_ASSETS, "icon.ico"))
        self.minsize(screen_width, screen_height)
        self.geometry(f"{screen_width}x{screen_height}+{x_coord}+{y_coord}")
        self.protocol(
            "WM_DELETE_WINDOW", lambda: self.player_leave(self.me, quitting=True)
        )
        self.bind("<Configure>", lambda e: self.win_resized(e))

    def win_resized(self, e):
        if e.widget == self:
            t = threading.Thread(target=self.resizer, args=((self.n + 1),))
            t.start()
            self.n += 1

    def resizer(self, n):
        sleep(0.1)
        if n == self.n:
            if self.property_frame.winfo_exists():
                self.property_frame.destroy()
                self.property_frame_popup(self.property_pos_displayed)
            self.n = 0

    def create_gui_divisions(self):
        self.board_canvas = tk.Canvas(
            self, width=self.board_side, height=self.board_side
        )
        self.board_canvas.place(relx=0.01, rely=0.06, anchor="nw")
        self.board_canvas.bind("<Button-1>", self.click_to_position)

        self.main_frame = tk.Frame(self)
        self.main_frame.place(
            relx=0.99, rely=0.06, relwidth=0.475, relheight=0.9, anchor="ne"
        )

        self.acc_button = tk.Button(
            self,
            image=self.player_details[self.me]["PFP"],
            text=f" {self.player_details[self.me]['Name']} ▾",
            highlightthickness=0,
            activebackground=self.cget("bg"),
            border=0,
            font=("times 14 bold"),
            compound="left",
            command=self.account_tab,
        )
        self.acc_button.place(relx=0.01, rely=0.03, anchor="w")
        self.acc_frame = tk.Frame()

        self.timer_label = tk.Label(self, font="consolas 12")
        self.timer_label.place(relx=0.1, rely=0.03, anchor="w")

    def create_image_obj(self):
        self.board_image = ImageTk.PhotoImage(
            Image.open(os.path.join(MONOPOLY_ASSETS, "BoardIMG.jpg")).resize(
                (self.board_side, self.board_side), Image.Resampling.LANCZOS
            )
        )
        self.board_canvas.create_image(2, 2, image=self.board_image, anchor="nw")

        self.info_tag = ImageTk.PhotoImage(
            Image.open(os.path.join(MONOPOLY_ASSETS, "info.png")).resize(
                (int(self.property_width / 2), int(self.property_width / 2)),
                Image.Resampling.LANCZOS,
            )
        )

        self.station_image = ImageTk.PhotoImage(
            Image.open(
                os.path.join(MONOPOLY_ASSETS, "utility_imgs", "station.png")
            ).resize(
                (int(2.5 * self.property_width), int(2.5 * self.property_width)),
                Image.Resampling.LANCZOS,
            )
        )

        self.water_image = ImageTk.PhotoImage(
            Image.open(
                os.path.join(MONOPOLY_ASSETS, "utility_imgs", "water.png")
            ).resize(
                (int(2.5 * self.property_width), int(2 * self.property_width)),
                Image.Resampling.LANCZOS,
            )
        )

        self.electric_image = ImageTk.PhotoImage(
            Image.open(
                os.path.join(MONOPOLY_ASSETS, "utility_imgs", "electric.png")
            ).resize(
                (int(2 * self.property_width), int(2.25 * self.property_width)),
                Image.Resampling.LANCZOS,
            )
        )

        self.dice1 = ImageTk.PhotoImage(
            Image.open(os.path.join(MONOPOLY_ASSETS, "die", "dice1.png")).resize(
                (int(0.9 * self.property_width), int(0.9 * self.property_width)),
                Image.Resampling.LANCZOS,
            )
        )
        self.dice2 = ImageTk.PhotoImage(
            Image.open(os.path.join(MONOPOLY_ASSETS, "die", "dice2.png")).resize(
                (int(0.9 * self.property_width), int(0.9 * self.property_width)),
                Image.Resampling.LANCZOS,
            )
        )
        self.dice3 = ImageTk.PhotoImage(
            Image.open(os.path.join(MONOPOLY_ASSETS, "die", "dice3.png")).resize(
                (int(0.9 * self.property_width), int(0.9 * self.property_width)),
                Image.Resampling.LANCZOS,
            )
        )
        self.dice4 = ImageTk.PhotoImage(
            Image.open(os.path.join(MONOPOLY_ASSETS, "die", "dice4.png")).resize(
                (int(0.9 * self.property_width), int(0.9 * self.property_width)),
                Image.Resampling.LANCZOS,
            )
        )
        self.dice5 = ImageTk.PhotoImage(
            Image.open(os.path.join(MONOPOLY_ASSETS, "die", "dice5.png")).resize(
                (int(0.9 * self.property_width), int(0.9 * self.property_width)),
                Image.Resampling.LANCZOS,
            )
        )
        self.dice6 = ImageTk.PhotoImage(
            Image.open(os.path.join(MONOPOLY_ASSETS, "die", "dice6.png")).resize(
                (int(0.9 * self.property_width), int(0.9 * self.property_width)),
                Image.Resampling.LANCZOS,
            )
        )
        self.roll_normal = ImageTk.PhotoImage(
            Image.open(os.path.join(MONOPOLY_ASSETS, "die", "roll_normal.png")).resize(
                (int(2.25 * self.property_width), int(0.8 * self.property_width)),
                Image.Resampling.LANCZOS,
            )
        )
        self.roll_disabled = ImageTk.PhotoImage(
            Image.open(
                os.path.join(MONOPOLY_ASSETS, "die", "roll_disabled.png")
            ).resize(
                (int(2.25 * self.property_width), int(0.8 * self.property_width)),
                Image.Resampling.LANCZOS,
            )
        )

        self.red_token_image = ImageTk.PhotoImage(
            Image.open(os.path.join(MONOPOLY_ASSETS, "tokens", "red.png")).resize(
                (self.token_width, self.token_width),
                Image.Resampling.LANCZOS,
            )
        )
        self.green_token_image = ImageTk.PhotoImage(
            Image.open(os.path.join(MONOPOLY_ASSETS, "tokens", "green.png")).resize(
                (self.token_width, self.token_width),
                Image.Resampling.LANCZOS,
            )
        )
        self.blue_token_image = ImageTk.PhotoImage(
            Image.open(os.path.join(MONOPOLY_ASSETS, "tokens", "blue.png")).resize(
                (self.token_width, self.token_width),
                Image.Resampling.LANCZOS,
            )
        )
        self.yellow_token_image = ImageTk.PhotoImage(
            Image.open(os.path.join(MONOPOLY_ASSETS, "tokens", "yellow.png")).resize(
                (self.token_width, self.token_width),
                Image.Resampling.LANCZOS,
            )
        )
        self.mr_monopoly = ImageTk.PhotoImage(
            Image.open(os.path.join(MONOPOLY_ASSETS, "mr_monopoly.png")).resize(
                (
                    int((self.board_side - 2) // 2.25),
                    int((self.board_side - 2) // 1.75),
                ),
                Image.Resampling.LANCZOS,
            )
        )
        tk.Label(
            self.main_frame,
            image=self.mr_monopoly,
            border=0,
            highlightthickness=0,
        ).place(relx=1, rely=1, relheight=0.575, relwidth=0.475, anchor="se")

        self.house_images = []

    def dice_tokens(self):
        self.die_dict = dict(
            zip(
                (1, 2, 3, 4, 5, 6),
                (
                    self.dice1,
                    self.dice2,
                    self.dice3,
                    self.dice4,
                    self.dice5,
                    self.dice6,
                ),
            )
        )

        self.roll_button = tk.Button(
            self.board_canvas,
            image=self.roll_normal,
            border=0,
            highlightthickness=0,
            activebackground="#d6f6e1",
            background="#d6f6e1",
            command=self.roll_dice,
        )
        self.roll_button.place(relx=0.5, rely=0.5, anchor="center")

        def dis_roll():
            while True:
                if str(self.roll_button["state"]) == "disabled":
                    self.roll_button.configure(image=self.roll_disabled)
                else:
                    self.roll_button.configure(image=self.roll_normal)

        t = threading.Thread(target=dis_roll, daemon=True)
        t.start()

        if self.turn != self.me:
            self.roll_button.configure(state="disabled")

        self.dice_spot1 = tk.Label(
            self.board_canvas,
            image=self.dice5,
            border=0,
            highlightthickness=0,
            bg="#d6f6e1",
        )
        self.dice_spot1.place(relx=0.485, rely=0.46, anchor="se")

        self.dice_spot2 = tk.Label(
            self.board_canvas,
            image=self.dice5,
            border=0,
            highlightthickness=0,
            bg="#d6f6e1",
        )
        self.dice_spot2.place(relx=0.515, rely=0.46, anchor="sw")

        self.red_token = tk.Button(
            self.board_canvas,
            image=self.red_token_image,
            border=0,
            highlightthickness=0,
            activebackground="#d6f6e1",
            command=lambda: self.open_children("red"),
        )

        self.green_token = tk.Button(
            self.board_canvas,
            image=self.green_token_image,
            border=0,
            highlightthickness=0,
            activebackground="#d6f6e1",
            command=lambda: self.open_children("green"),
        )

        self.blue_token = tk.Button(
            self.board_canvas,
            image=self.blue_token_image,
            border=0,
            activebackground="#d6f6e1",
            highlightthickness=0,
            command=lambda: self.open_children("blue"),
        )

        self.yellow_token = tk.Button(
            self.board_canvas,
            image=self.yellow_token_image,
            border=0,
            highlightthickness=0,
            activebackground="#d6f6e1",
            command=lambda: self.open_children("gold"),
        )

    def account_tab(self):
        if self.acc_frame.winfo_ismapped():
            self.unbind("<Button-1>")
            self.acc_frame.place_forget()
        else:

            def clicked(e):
                if self.acc_frame.winfo_containing(e.x_root, e.y_root) not in [
                    self.quit_button,
                    self.end_game_button,
                    self.acc_frame,
                    self.acc_button,
                    self.theme_button,
                ]:
                    self.acc_frame.place_forget()
                    self.unbind("<Button-1>")

            self.bind("<Button-1>", lambda e: clicked(e))
            self.acc_frame = tk.Frame(self)
            self.acc_frame.place(relx=0.01, rely=0.06, anchor="nw")

            def end_game_now():
                if self.show_message(
                    "End Game?",
                    "Are you sure you wish to end this game? Game will end only based on other players' opinions!",
                    type="okcancel",
                ):
                    self.poll(
                        self.me,
                        (
                            "CREATE",
                            "endgame",
                            False,
                            self.player_details[self.me]["Name"],
                        ),
                    )
                self.acc_frame.place_forget()
                self.unbind("<Button-1>")

            def q():
                self.send_leave("ENDED")
                self.quit_game()

            self.quit_button = ttk.Button(
                self.acc_frame,
                text="Forfeit" if not self.isEnded else "QUIT",
                style="12.TButton",
                command=(lambda: self.player_leave(self.me, quitting=True))
                if not self.isEnded
                else q,
            )
            self.quit_button.grid(row=0, column=0, columnspan=2, sticky="nsew", pady=2)

            if not (self.isEnding or self.isEnded):
                self.end_game_button = ttk.Button(
                    self.acc_frame,
                    text="End Game",
                    style="12.TButton",
                    command=end_game_now,
                )
                self.end_game_button.grid(
                    row=1, column=0, columnspan=2, sticky="nsew", pady=2
                )

            theme_var = tk.StringVar(value=CURR_THEME)

            def tog():
                global CURR_THEME
                CURR_THEME = theme_var.get()
                theme.toggle_theme()

            tk.Label(self.acc_frame, text="Dark Mode", font=("times", 12)).grid(
                row=2, column=0, sticky="e", pady=2
            )
            self.theme_button = ttk.Checkbutton(
                self.acc_frame,
                style="Switch.TCheckbutton",
                variable=theme_var,
                onvalue="dark",
                offvalue="light",
                command=tog,
            )
            self.theme_button.grid(row=2, column=1, sticky="e", pady=2)

    # endregion

    # region # Util

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

    def count_colour(self, propertypos):
        owner = self.properties[propertypos].owner
        if owner:
            colour = self.properties[propertypos].colour
            c = 0
            for i in self.player_details[owner]["Properties"]:
                if i.colour == colour:
                    c += 1
            return c
        else:
            return None

    def owner_detail(self, propertypos, s="Name"):
        return self.player_details[self.properties[propertypos].owner][s]

    def isBankrupt(self, amt_to_pay, payer):
        check = 0
        for i in self.player_details[payer]["Properties"]:
            if not i.isMortgaged:
                if i.houses > 0:
                    check += i.houses
                check += i.mortgage

        if amt_to_pay <= check + self.player_details[payer]["Money"]:
            return False
        else:
            return True

    # endregion

    # region # Update Game

    def update_game(self, action_frame_text=None, playerleft=None):
        if self.property_frame.winfo_exists():
            self.property_frame.destroy()
            self.property_frame_popup(self.property_pos_displayed)
        l = []
        for i in self.player_details:
            if self.player_tree.item(i, "open"):
                l.append(i)
        self.player_tree.destroy()
        self.player_frame_popup(l)
        self.house_images = []
        self.place_houses()
        self.action_frame.destroy()
        if playerleft:
            self.action_frame_popup(f"{playerleft} is bankrupt!")
        else:
            if action_frame_text:
                self.action_frame_popup(action_frame_text)
            else:
                self.action_frame_popup(self.current_txt)
        if self.turn != self.me:
            self.roll_button.configure(state="disabled")

        try:
            self.acc_frame.place_forget()
            self.unbind("<Button-1>")
        except:
            pass

    def toggle_action_buttons(self, enable=False):
        if enable:
            state = "normal"
        else:
            state = "disabled"
        d = {
            "end": self.end_button,
            "buy": self.buy_button,
            "build": self.build_button,
            "mortgage": self.mortgage_button,
            "trade": self.trade_button,
            "unmortgage": self.unmortgage_button,
            "sell": self.sell_button,
        }
        for i in d:
            if d[i].winfo_exists():
                d[i].configure(state=state)
                if i == "end":
                    if str(self.roll_button["state"]) == "normal":
                        d[i].configure(state="disabled")
                elif i == "mortgage":
                    if not self.player_details[self.turn]["Properties"]:
                        d[i].configure(state="disabled")
                    else:
                        l = [
                            i
                            for i in self.player_details[self.turn]["Properties"]
                            if i.houses <= 0 and not i.isMortgaged
                        ]
                        if not l:
                            d[i].configure(state="disabled")
                elif i == "build":
                    my_sets = self.find_my_sets()
                    if not my_sets:
                        d[i].configure(state="disabled")
                elif i == "buy":
                    if (
                        not bool(
                            self.properties[
                                self.player_details[self.turn]["Position"] % 40
                            ].colour
                        )
                        or (
                            self.properties[
                                self.player_details[self.turn]["Position"] % 40
                            ].owner
                        )
                        or self.isBankrupt(
                            self.properties[
                                self.player_details[self.turn]["Position"] % 40
                            ].price,
                            self.turn,
                        )
                    ):
                        d[i].configure(state="disabled")
                elif i == "sell":
                    if not any(
                        i.houses > 0
                        for i in self.player_details[self.turn]["Properties"]
                    ):
                        self.sell_button.configure(state="disabled")
                elif i == "unmortgage":
                    if not any(
                        i.isMortgaged
                        for i in self.player_details[self.turn]["Properties"]
                    ):
                        self.unmortgage_button.configure(state="disabled")

    def end_turn(self, received=False, force=False):
        self.toggle_action_buttons()
        if not received and not force:
            if self.show_message(
                "End Turn?",
                f"{self.player_details[self.turn]['Name']}, are you sure you want to end your turn?",
                type="yesno",
            ):
                pass
            else:
                self.update_game()
                self.toggle_action_buttons(True)
                return
        try:
            self.turn = self.uuids[self.uuids.index(self.turn) + 1]
        except:
            self.turn = self.uuids[0]

        self.timer.stop()
        if not (received or force):
            self.send_msg(("END",))

        if self.turn == self.me:
            self.roll_button.configure(state="normal")
            self.bg_timer_thr = threading.Thread(
                target=self.timer_init,
                args=(
                    600,
                    lambda: self.player_leave(self.me, inactive=True),
                    "Inactivity Timer",
                ),
                daemon=True,
            )
            self.bg_timer_thr.start()
            if self.player_details[self.turn]["Injail"][0]:
                if self.player_details[self.turn]["Injail"][1] == 0:
                    text = "Do you wish to pay 50"
                    if self.player_details[self.turn]["GOJF"]:
                        text += " (or Use your Get out of Jail Free Card) now?"
                    else:
                        text += " now?"
                    if self.show_message(
                        "You are in jail! Pay Now?",
                        text
                        + " If no, you have to roll doubles in the next 3 turns to get out of Jail.",
                        type="yesno",
                    ):
                        self.ask_pay_jail()
                    else:
                        self.update_game("Roll doubles to get out of jail!")
                elif self.player_details[self.turn]["Injail"][1] == 2:
                    text = "Roll Doubles to get out of jail or you have to"
                    if self.player_details[self.turn]["GOJF"]:
                        text += "\nPay 50 or Use your Get out of Jail Free Card"
                    else:
                        text += " Pay 50"
                    self.update_game(text)
                else:
                    self.update_game("Roll doubles to get out of jail!")
            else:
                self.update_game("It's your turn now! Click on Roll Dice")
        self.update_game()

    # endregion

    # region # Timers

    def timer_init(self, time, func, name, precision="minsec"):
        self.timer = Timer(time)
        self.timer.start()
        if self.timer_display_thread:
            self.timer_display_thread.stop()
            self.timer_display_thread = None
        self.timer_display_thread = StoppableThread(
            lambda: self.display_timer(self.timer, self.timer_label, precision, name),
            self.timer.is_alive,
            0.005,
        )
        self.timer_display_thread.start()
        while True:
            if self.timer.time_left() <= 0:
                self.timer.stop()
                func()
                break

    @staticmethod
    def display_timer(timer: Timer, lbl: tk.Label, precision="sec", init_txt=""):
        a = round(timer.time_left(), 2)
        if a < 0.01:
            min, sec, ms = 0, 0, 0
        min, sec, ms = int(a // 60), int(a % 60), int(a * 100 % 100)
        if precision == "sec":
            things = "{:02d}".format(sec)
        elif precision == "minsec":
            things = "{:02d}:{:02d}".format(min, sec)
        else:
            things += "{:02d}:{:02d}:{:02d}".format(min, sec, ms)
        lbl.configure(text=init_txt + " → " + things)

    # endregion

    # region # Roll, Move

    def roll_dice(self, roll=None, received=False, cli=False):
        self.timer.reset()
        try:
            music(os.path.join(MONOPOLY_ASSETS, "die", "diceroll.mp3"))
        except:
            pass
        self.roll_button.configure(state="disabled")
        dice_roll = roll if received else (random.randint(1, 6), random.randint(1, 6))
        dice_roll = roll if cli else dice_roll
        if not received:
            self.send_msg(("ROLL", dice_roll))
        for i in range(18):
            self.dice_spot1.configure(image=self.die_dict[random.randint(1, 6)])
            self.dice_spot2.configure(image=self.die_dict[random.randint(1, 6)])
            self.dice_spot1.update()
            self.dice_spot2.update()
            sleep(0.12)
        self.dice_spot1.configure(image=self.die_dict[dice_roll[0]])
        self.dice_spot2.configure(image=self.die_dict[dice_roll[1]])
        self.dice_spot1.update()
        self.dice_spot2.update()
        self.current_move = sum(dice_roll)
        if self.player_details[self.turn]["Injail"][0]:
            if dice_roll[0] == dice_roll[1]:
                self.player_details[self.turn]["Injail"][0] = False
                self.move(self.turn, 0)
                self.player_details[self.turn]["Injail"][1] = 0
                self.move(self.turn, self.current_move, endturn=True)
            else:
                if self.player_details[self.turn]["Injail"][1] < 2:
                    self.update_game("Try again next turn!")
                    try:
                        self.end_button.configure(state="normal")
                    except:
                        pass
                    self.player_details[self.turn]["Injail"][1] += 1
                else:
                    self.ask_pay_jail()
        else:
            if dice_roll[0] == dice_roll[1]:
                self.timer.reset()
                self.doubles_counter += 1
                if self.doubles_counter == 3:
                    self.doubles_counter = 0
                    self.go_to_jail(self.turn)
                else:
                    self.move(self.turn, self.current_move, endturn=False)
            else:
                self.doubles_counter = 0
                self.move(self.turn, self.current_move, endturn=True)

    def click_to_position(self, event):
        x, y = event.x, event.y
        l = [1.6, 1.6]
        l[1:1] = [1] * 9
        pos = None
        if x <= self.property_height:
            for i in range(len(l)):
                if y > sum(l[i + 1 :]) / sum(l) * self.board_side:
                    pos = 10 + i
                    break
        elif x >= self.board_side - self.property_height:
            for i in range(len(l)):
                if y > sum(l[i + 1 :]) / sum(l) * self.board_side:
                    pos = (40 - i) % 40
                    break
        elif y <= self.property_height:
            for i in range(len(l)):
                if x > sum(l[i + 1 :]) / sum(l) * self.board_side:
                    pos = 30 - i
                    break
        elif y >= self.board_side - self.property_height:
            for i in range(len(l)):
                if x > sum(l[i + 1 :]) / sum(l) * self.board_side:
                    pos = i
                    break
        if pos in [10, 30]:
            self.show_message("Jail Rules", "Jail Rules", timeout=2000)
        elif pos == 20:
            self.show_message("Free Parking", "Do Nothing!", timeout=2000)
        elif pos == 0:
            self.show_message("GO!", "Collect 200 Salary as you pass GO!", timeout=2000)
        elif pos in [2, 17, 33]:
            self.show_message("Community Chest", "Do as directed on card", timeout=2000)
        elif pos in [7, 22, 36]:
            self.show_message("Chance", "Do as directed on card", timeout=2000)
        elif pos == 4:
            self.show_message(
                "Income Tax", "Pay 200 as Tax on landing here", timeout=2000
            )
        elif pos == 38:
            self.show_message(
                "Super Tax", "Pay 100 as Tax on landing here", timeout=2000
            )
        elif pos:
            self.property_frame_popup(pos)

    def position_to_xy(
        self, position
    ):  # +1, +2, because canvas has random error and places image 2,2 up and left, so image is placed at 2,2 and not 0,0
        l = [1.6, 1.6]
        l[1:1] = [1] * 9
        position %= 40
        if position == 0:
            x1 = self.board_side + 1
            y1 = self.board_side - self.property_height + 2
        elif position <= 10:
            x1 = sum(l[:-(position)]) * self.property_width + 1
            y1 = self.board_side - self.property_height + 2
        elif position <= 20:
            x1 = self.property_height + 2
            y1 = sum(l[: -(position - 9)]) * self.property_width + 1
        elif position <= 30:
            x1 = sum(l[: (position - 19)]) * self.property_width + 1
            y1 = 0 + 2
        elif position < 40:
            x1 = self.board_side + 2
            y1 = sum(l[: (position - 30)]) * self.property_width + 1
        # self.board_canvas.create_rectangle(x1,y1,x1-self.property_height,y1+self.property_height,outline='blue',width=3)
        return x1, y1

    def position_to_tokenxy(self, player, position):
        position %= 40

        x1, y1 = self.position_to_xy(position)
        if position == 10:
            if self.player_details[player]["Injail"][0]:
                x = x1 - (self.property_height * 0.35)
                y = y1 + (self.property_height * 0.35)
            else:
                if self.player_details[player]["Colour"] == "red":
                    return int(
                        self.token_width / 2 + self.property_height * 0.075
                    ), int(y1 + self.property_height * 0.3 - self.token_width / 2)
                elif self.player_details[player]["Colour"] == "green":
                    return int(
                        self.token_width / 2 + self.property_height * 0.075
                    ), int(y1 + self.property_height * 0.6 - self.token_width / 2)
                elif self.player_details[player]["Colour"] == "blue":
                    return int(
                        x1 - self.property_height * 0.6 + self.token_width / 2 + 3
                    ), int(y1 + self.property_height * 0.95 - self.token_width / 2)
                elif self.player_details[player]["Colour"] == "gold":
                    return int(
                        x1 - self.property_height * 0.3 + self.token_width / 2 + 3
                    ), int(y1 + self.property_height * 0.95 - self.token_width / 2)
                else:
                    print("Position Error")
        elif not position % 10:
            x = x1 - (self.property_height * 0.5)
            y = y1 + (self.property_height * 0.5)
        elif position < 10:
            x = x1 - (self.property_width * 0.5)
            y = y1 + (self.property_height * 0.6)
        elif position < 20:
            x = x1 - (self.property_height * 0.6)
            y = y1 + (self.property_width * 0.5)
        elif position < 30:
            x = x1 - (self.property_width * 0.5)
            y = y1 + (self.property_height * 0.4)
        elif position < 40:
            x = x1 - (self.property_height * 0.4)
            y = y1 + (self.property_width * 0.5)

        if self.player_details[player]["Colour"] == "red":
            return int(x - self.token_width / 2 - 1), int(y - self.token_width / 2)
        elif self.player_details[player]["Colour"] == "green":
            return int(x + self.token_width / 2 + 1), int(y - self.token_width / 2)
        elif self.player_details[player]["Colour"] == "blue":
            return int(x - self.token_width / 2 - 1), int(y + self.token_width / 2 + 2)
        elif self.player_details[player]["Colour"] == "gold":
            return int(x + self.token_width / 2 + 1), int(y + self.token_width / 2 + 2)

    def move(self, player, move, endturn=False, showmove=True):
        colour = self.player_details[player]["Colour"]
        self.colour_token_dict = {
            "red": self.red_token,
            "green": self.green_token,
            "blue": self.blue_token,
            "gold": self.yellow_token,
        }

        if move and showmove:
            for i in range(move):
                self.player_details[player]["Position"] += 1
                x1, y1 = self.position_to_tokenxy(
                    player, self.player_details[player]["Position"]
                )
                self.colour_token_dict[colour].place(x=x1, y=y1, anchor="center")
                sleep(0.2)
                self.colour_token_dict[colour].update()
                if not self.player_details[player]["Position"] % 40:
                    self.pass_go(player)
        else:
            self.player_details[player]["Position"] += move
            x1, y1 = self.position_to_tokenxy(
                player, self.player_details[player]["Position"]
            )
            self.colour_token_dict[colour].place(x=x1, y=y1, anchor="center")

        pos = self.player_details[player]["Position"] % 40

        if endturn:
            self.roll_button.configure(state="disabled")
            if self.end_button.winfo_exists():
                self.end_button.configure(state="normal")
            if self.me == player and pos not in [2, 17, 33, 7, 22, 36]:
                self.timer.stop()
                self.end_timer_thr = threading.Thread(
                    target=self.timer_init,
                    args=(
                        60,
                        lambda: self.end_turn(force=True),
                        "Time Left for Turn to End",
                        "sec",
                    ),
                    daemon=True,
                )
                self.end_timer_thr.start()
        else:
            if move:
                self.timer.reset()
            self.roll_button.configure(state="normal")
            if self.end_button.winfo_exists():
                self.end_button.configure(state="disabled")

        self.player_details[player]["PLACES"].update(
            {
                self.properties[pos]
                .name: self.player_details[player]["PLACES"]
                .get(self.properties[pos].name, 0)
                + 1
            }
        )
        if pos == 30:
            self.go_to_jail(self.turn)
        elif pos == 4:
            self.pay(self.turn, 200)
        elif pos == 38:
            self.pay(self.turn, 100)
        elif pos in [0, 10, 20]:
            self.update_game()
        elif pos in [2, 17, 33]:
            self.update_game(self.community())
        elif pos in [7, 22, 36]:
            self.update_game(self.chance())
        elif pos:
            self.property_frame_popup(pos)
            if self.properties[pos].owner:
                if self.properties[pos].owner != self.turn:
                    if self.properties[pos].isMortgaged:
                        self.update_game("This property is Mortgaged!")
                    else:
                        self.pay(
                            self.turn,
                            self.properties[pos].rent(self.current_move),
                            self.properties[pos].owner,
                        )
                else:
                    if self.properties[pos].isMortgaged:
                        self.update_game(
                            "You own this mortgaged property! Unmortgage to start receiving rent when others land here."
                        )
                    else:
                        self.update_game("You own this property!")
            else:
                if self.isBankrupt(
                    self.properties[pos].price,
                    self.turn,
                ):
                    self.update_game("You don't have enough cash to buy this property!")
                else:
                    self.update_game("Click Buy to buy this property!")
                    if self.turn == self.me:
                        self.buy_button.configure(state="normal")

    # endregion

    # region # Jail

    def go_to_jail(self, player):
        self.player_details[player]["Injail"][0] = True
        move = (10 - self.player_details[player]["Position"] % 40) % 40
        self.move(player, move, showmove=False, endturn=True)
        text = "You are in jail! Roll Doubles in the next 3 turns"
        if self.player_details[player]["GOJF"]:
            text += ",\nPay 50 or Use your Get out of Jail Free Card"
        else:
            text += " or Pay 50"
        self.action_frame_popup(text)
        sleep(2)
        self.end_turn(force=True)
        self.update_game()

    def ask_pay_jail(self):
        if self.turn == self.me:
            if self.player_details[self.turn]["GOJF"]:
                if self.show_message(
                    "Use Get out of Jail Free?",
                    "Do you want to use your Get out of Jail Free Card? If not, you'll have to pay 50!",
                    type="yesno",
                ):
                    self.out_of_jail("GOJF")
                else:
                    self.out_of_jail("PAY")
            else:
                self.out_of_jail("PAY")

    def out_of_jail(self, method, received=False):
        if method == "GOJF":
            self.player_details[self.turn]["GOJF"] -= 1
            self.chance.add_back()
            self.community.add_back()
        elif method == "PAY":
            self.pay(self.turn, 50)

        self.player_details[self.turn]["Injail"][0] = False
        self.move(self.turn, 0)
        self.player_details[self.turn]["Injail"][1] = 0
        self.update_game("You're out of jail now! Click on Roll Dice")

        if not received:
            self.send_msg(("JAIL", method))

    # endregion

    # region # Property Frame

    def station_property_frame(self, position):
        station_label = tk.Label(
            self.property_frame,
            image=self.station_image,
            border=0,
            highlightthickness=0,
        )
        station_label.place(relx=0.5, rely=0.2, anchor="center")

        tk.Label(
            self.property_frame,
            text=self.properties[position].name.upper(),
            font=("times", (self.board_side - 2) // 40),
            bg="#F9FBFF",
            fg="black",
        ).place(relx=0.5, rely=0.4, anchor="center")

        tk.Button(
            self.property_frame,
            text="✕",
            font=("courier", (self.board_side - 2) // 60),
            fg="black",
            activeforeground="black",
            bg="#F9FBFF",
            highlightthickness=0,
            border=0,
            activebackground=self.property_frame.cget("bg"),
            command=self.property_frame.destroy,
        ).place(relx=0.95, rely=0.05, anchor="ne")

        canvas = tk.Canvas(
            self.property_frame,
            highlightthickness=0,
            bg="#F9FBFF",
        )
        canvas.place(relx=0.5, rely=0.7, relheight=0.55, relwidth=0.9, anchor="center")
        canvas.update()
        y_coord = canvas.winfo_height() / 12

        ttk.Separator(canvas, orient="horizontal").place(
            relx=0.5, rely=0.85, anchor="center", relwidth=0.8
        )
        ttk.Separator(canvas, orient="horizontal").place(
            relx=0.5, rely=0.15, anchor="center", relwidth=0.8
        )

        tk.Button(
            self.property_frame,
            image=self.info_tag,
            border=0,
            highlightthickness=0,
            activebackground=self.property_frame.cget("bg"),
            command=lambda: self.show_message(
                "Station Rules", "Station Rules", timeout=2000
            ),
        ).place(x=35, rely=0.925, anchor="center")

        row_counter = 0
        stations_data = {
            "Unowned; Buy For": self.properties[position].price,
            "Rent": 25,
            "If 2 Stations are owned": 50,
            "If 3 Stations are owned": 100,
            "If 4 Stations are owned": 200,
        }
        for (
            i,
            j,
        ) in stations_data.items():  # Placing and formatting Rent data on card
            row_counter += 1
            try:
                if row_counter == self.count_colour(position) + 1:
                    canvas.create_text(
                        2,
                        y_coord - 2,
                        anchor="w",
                        text="▶",
                        font=("times", (self.board_side - 2) // 32),
                        fill=self.owner_detail(position, "Colour"),
                    )
            except:
                pass
            if row_counter == 1:
                if self.properties[position].owner:
                    canvas.create_text(
                        canvas.winfo_width() / 2,
                        y_coord,
                        anchor="center",
                        text=f"Owner: {self.owner_detail(position,'Name')}",
                        font=("times", (self.board_side - 2) // 45),
                        fill=self.owner_detail(position, "Colour"),
                    )
                else:
                    canvas.create_text(
                        2,
                        y_coord - 2,
                        anchor="w",
                        text="▶",
                        font=("times", (self.board_side - 2) // 32),
                    )
                    canvas.create_text(
                        25,
                        y_coord,
                        anchor="w",
                        text=i,
                        font=("times", (self.board_side - 2) // 45),
                    )
                    canvas.create_text(
                        canvas.winfo_width() / 1.3,
                        y_coord,
                        text="₩",
                        angle=180,
                        font=("courier", (self.board_side - 2) // 45),
                    )
                    canvas.create_text(
                        canvas.winfo_width() - 25,
                        y_coord,
                        anchor="e",
                        text=str(j),
                        font=("times", (self.board_side - 2) // 45),
                    )
            else:
                canvas.create_text(
                    25,
                    y_coord,
                    anchor="w",
                    text=i,
                    font=("times", (self.board_side - 2) // 45),
                )
                canvas.create_text(
                    canvas.winfo_width() / 1.3,
                    y_coord,
                    text="₩",
                    angle=180,
                    font=("courier", (self.board_side - 2) // 45),
                )
                canvas.create_text(
                    canvas.winfo_width() - 25,
                    y_coord,
                    anchor="e",
                    text=str(j),
                    font=("times", (self.board_side - 2) // 45),
                )

            y_coord += canvas.winfo_height() / 6
        canvas.create_text(
            45,
            y_coord,
            anchor="w",
            text="Mortgage Value",
            font=("times", (self.board_side - 2) // 51),
        )
        canvas.create_text(
            canvas.winfo_width() / 1.3,
            y_coord,
            text="₩",
            angle=180,
            font=("courier", (self.board_side - 2) // 51),
        )
        canvas.create_text(
            canvas.winfo_width() - 35,
            y_coord,
            anchor="e",
            text=self.properties[position].mortgage,
            font=("times", (self.board_side - 2) // 51),
        )

    def utility_property_frame(self, position):
        if position == 28:
            utility_image = self.water_image
        else:
            utility_image = self.electric_image
        utility_label = tk.Label(
            self.property_frame, image=utility_image, border=0, highlightthickness=0
        )
        utility_label.place(relx=0.5, rely=0.2, anchor="center")

        tk.Label(
            self.property_frame,
            text=self.properties[position].name.upper(),
            font=("times", (self.board_side - 2) // 40),
            bg="#F9FBFF",
            fg="black",
        ).place(relx=0.5, rely=0.4, anchor="center")

        tk.Button(
            self.property_frame,
            text="✕",
            font=("courier", (self.board_side - 2) // 60),
            fg="black",
            activeforeground="black",
            bg="#F9FBFF",
            highlightthickness=0,
            border=0,
            activebackground=self.property_frame.cget("bg"),
            command=self.property_frame.destroy,
        ).place(relx=0.95, rely=0.05, anchor="ne")

        canvas = tk.Canvas(
            self.property_frame,
            highlightthickness=0,
            bg="#F9FBFF",
        )
        canvas.place(relx=0.5, rely=0.7, relheight=0.55, relwidth=0.9, anchor="center")
        canvas.update()
        y_coord = canvas.winfo_height() / 14

        ttk.Separator(canvas, orient="horizontal").place(
            relx=0.5, rely=0.85, anchor="center", relwidth=0.8
        )

        ttk.Separator(canvas, orient="horizontal").place(
            relx=0.5, rely=0.15, anchor="center", relwidth=0.8
        )

        tk.Button(
            self.property_frame,
            image=self.info_tag,
            border=0,
            highlightthickness=0,
            activebackground=self.property_frame.cget("bg"),
            command=lambda: self.show_message(
                "Utility Rules", "Utility Rules", timeout=2000
            ),
        ).place(x=35, rely=0.925, anchor="center")

        row_counter = 0
        try:  # if dice has been rolled
            utilities_data = {
                "Unowned; Buy For": self.properties[position].price,
                f"Rent based on last roll ({self.current_move}),": None,
                "If 1 utility is owned:": None,
                f" 4   x  {self.current_move}     = ": 4 * self.current_move,
                "If 2 utilities are owned:": None,
                f"10  x  {self.current_move}     =": 10 * self.current_move,
            }
        except:  # if dice has not been rolled yet
            utilities_data = {
                "Unowned; Buy For": self.properties[position].price,
                "Rent based on roll (10),": None,
                "If 1 utility is owned:": None,
                f" 4   x  10     = ": 40,
                "If 2 utilities are owned:": None,
                f"10  x  10     =": 100,
            }
        for (
            i,
            j,
        ) in utilities_data.items():  # Placing and formatting Rent data on card
            row_counter += 1
            try:
                if row_counter == self.count_colour(position) * 2 + 1:
                    canvas.create_text(
                        2,
                        y_coord - 2,
                        anchor="w",
                        text="▶",
                        font=("times", (self.board_side - 2) // 32),
                        fill=self.owner_detail(position, "Colour"),
                    )
            except:
                pass
            if row_counter == 1:
                if self.properties[position].owner:
                    canvas.create_text(
                        canvas.winfo_width() / 2,
                        y_coord,
                        anchor="center",
                        text=f"Owner: {self.owner_detail(position,'Name')}",
                        font=("times", (self.board_side - 2) // 45),
                        fill=self.owner_detail(position, "Colour"),
                    )
                else:
                    canvas.create_text(
                        2,
                        y_coord - 2,
                        anchor="w",
                        text="▶",
                        font=("times", (self.board_side - 2) // 32),
                    )
                    canvas.create_text(
                        25,
                        y_coord,
                        anchor="w",
                        text=i,
                        font=("times", (self.board_side - 2) // 45),
                    )
                    canvas.create_text(
                        canvas.winfo_width() / 1.3,
                        y_coord,
                        text="₩",
                        angle=180,
                        font=("courier", (self.board_side - 2) // 45),
                    )
                    canvas.create_text(
                        canvas.winfo_width() - 25,
                        y_coord,
                        anchor="e",
                        text=str(j),
                        font=("times", (self.board_side - 2) // 45),
                    )
            elif row_counter in [2, 3, 5]:  # text row
                canvas.create_text(
                    25,
                    y_coord,
                    anchor="w",
                    text=i,
                    font=("times", (self.board_side - 2) // 45),
                )
            elif row_counter in [4, 6]:  # rent row
                canvas.create_text(
                    canvas.winfo_width() / 2.75,
                    y_coord,
                    anchor="w",
                    text=i,
                    font=("times", (self.board_side - 2) // 45),
                )
                canvas.create_text(
                    canvas.winfo_width() / 1.3,
                    y_coord,
                    text="₩",
                    angle=180,
                    font=("courier", (self.board_side - 2) // 45),
                )
                canvas.create_text(
                    canvas.winfo_width() - 25,
                    y_coord,
                    anchor="e",
                    text=str(j),
                    font=("times", (self.board_side - 2) // 45),
                )

            y_coord += canvas.winfo_height() / 7
        canvas.create_text(
            45,
            y_coord,
            anchor="w",
            text="Mortgage Value",
            font=("times", (self.board_side - 2) // 51),
        )
        canvas.create_text(
            canvas.winfo_width() / 1.3,
            y_coord,
            text="₩",
            angle=180,
            font=("courier", (self.board_side - 2) // 51),
        )
        canvas.create_text(
            canvas.winfo_width() - 35,
            y_coord,
            anchor="e",
            text=self.properties[position].mortgage,
            font=("times", (self.board_side - 2) // 51),
        )

    def colour_property_frame(self, position):
        title_frame = tk.Frame(
            self.property_frame,
            bg=self.properties[position].hex,
            highlightthickness=2,
            highlightbackground="black",
        )
        title_frame.place(
            relx=0.5, rely=0.125, relwidth=0.9, relheight=0.2, anchor="center"
        )

        tk.Label(
            title_frame,
            text="TITLE DEED",
            font=("times", (self.board_side - 2) // 56),
            bg=self.properties[position].hex,
            fg="black",
        ).place(relx=0.5, rely=0.25, anchor="center")

        tk.Label(
            title_frame,
            text=self.properties[position].name.upper(),
            font=("times", (self.board_side - 2) // 42),
            bg=self.properties[position].hex,
            fg="black",
        ).place(relx=0.5, rely=0.65, anchor="center")

        tk.Button(
            title_frame,
            text="✕",
            font=("courier", (self.board_side - 2) // 60),
            fg="black",
            activeforeground="black",
            bg=self.properties[position].hex,
            highlightthickness=0,
            border=0,
            activebackground=self.properties[position].hex,
            command=self.property_frame.destroy,
        ).place(relx=1, rely=0, anchor="ne")

        canvas = tk.Canvas(
            self.property_frame,
            highlightthickness=0,
            bg="#F9FBFF",
        )
        canvas.place(relx=0.5, rely=0.6, relheight=0.7, relwidth=0.9, anchor="center")

        canvas.update()
        y_coord = canvas.winfo_height() / 23

        ttk.Separator(canvas, orient="horizontal").place(
            relx=0.5, rely=0.725, anchor="center", relwidth=0.8
        )

        ttk.Separator(canvas, orient="horizontal").place(
            relx=0.5, rely=0.09, anchor="center", relwidth=0.8
        )

        tk.Button(
            self.property_frame,
            image=self.info_tag,
            border=0,
            highlightthickness=0,
            activebackground=self.property_frame.cget("bg"),
            command=lambda: self.show_message(
                "Hotel Rules", "Hotel Rules", timeout=2000
            ),
        ).place(x=35, rely=0.9, anchor="center")

        vals = [self.properties[position].price]
        vals.extend(self.properties[position].rent_values)
        vals.extend(
            [
                self.properties[position].mortgage,
                self.properties[position].build,
                self.properties[position].build,
            ]
        )
        d = dict(
            zip(
                [
                    "Unowned; Buy For",
                    "Rent",
                    "With Color Set",
                    "With 1 House",
                    "With 2 Houses",
                    "With 3 Houses",
                    "With 4 Houses",
                    "With Hotel",
                    "Mortgage Value",
                    "House Cost",
                    "Hotel Cost",
                ],
                vals,
            )
        )

        row_counter = -3
        for i, j in d.items():  # Placing and formatting Rent data on card
            row_counter += 1
            try:
                if row_counter == self.properties[position].houses:
                    canvas.create_text(
                        2,
                        y_coord - 2,
                        anchor="w",
                        text="▶",
                        font=("times", (self.board_side - 2) // 32),
                        fill=self.owner_detail(position, "Colour"),
                    )
            except:
                pass

            if row_counter == -2:
                if self.properties[position].owner:
                    canvas.create_text(
                        canvas.winfo_width() / 2,
                        y_coord,
                        anchor="center",
                        text=f"Owner: {self.owner_detail(position,'Name')}",
                        font=("times", (self.board_side - 2) // 45),
                        fill=self.owner_detail(position, "Colour"),
                    )
                else:
                    canvas.create_text(
                        2,
                        y_coord - 2,
                        anchor="w",
                        text="▶",
                        font=("times", (self.board_side - 2) // 32),
                    )
                    canvas.create_text(
                        25,
                        y_coord,
                        anchor="w",
                        text=i,
                        font=("times", (self.board_side - 2) // 45),
                    )
                    canvas.create_text(
                        canvas.winfo_width() / 1.375,
                        y_coord,
                        text="₩",
                        angle=180,
                        font=("courier", (self.board_side - 2) // 45),
                    )
                    canvas.create_text(
                        canvas.winfo_width() - 25,
                        y_coord,
                        anchor="e",
                        text=str(j),
                        font=("times", (self.board_side - 2) // 45),
                    )
            if row_counter in [-1, 0]:  # rent, double rent
                canvas.create_text(
                    25,
                    y_coord,
                    anchor="w",
                    text=i,
                    font=("times", (self.board_side - 2) // 42),
                )
                canvas.create_text(
                    canvas.winfo_width() / 1.375,
                    y_coord,
                    text="₩",
                    angle=180,
                    font=("courier", (self.board_side - 2) // 42),
                )
                canvas.create_text(
                    canvas.winfo_width() - 25,
                    y_coord,
                    anchor="e",
                    text=str(j),
                    font=("times", (self.board_side - 2) // 42),
                )
            elif row_counter in [1, 2, 3, 4]:  # houses
                canvas.create_text(
                    25,
                    y_coord,
                    anchor="w",
                    text=i,
                    font=("times", (self.board_side - 2) // 42),
                    fill="green",
                )
                canvas.create_text(
                    canvas.winfo_width() / 1.375,
                    y_coord,
                    text="₩",
                    angle=180,
                    font=("courier", (self.board_side - 2) // 42),
                    fill="green",
                )
                canvas.create_text(
                    canvas.winfo_width() - 25,
                    y_coord,
                    anchor="e",
                    text=str(j),
                    font=("times", (self.board_side - 2) // 42),
                    fill="green",
                )
            elif row_counter == 5:  # hotel
                canvas.create_text(
                    25,
                    y_coord,
                    anchor="w",
                    text=i,
                    font=("times", (self.board_side - 2) // 42),
                    fill="red",
                )
                canvas.create_text(
                    canvas.winfo_width() / 1.375,
                    y_coord,
                    text="₩",
                    angle=180,
                    font=("courier", (self.board_side - 2) // 42),
                    fill="red",
                )
                canvas.create_text(
                    canvas.winfo_width() - 25,
                    y_coord,
                    anchor="e",
                    text=str(j),
                    font=("times", (self.board_side - 2) // 42),
                    fill="red",
                )
            elif row_counter == 6:  # mortgage
                canvas.create_text(
                    45,
                    y_coord,
                    anchor="w",
                    text=i,
                    font=("times", (self.board_side - 2) // 49),
                )
                canvas.create_text(
                    canvas.winfo_width() / 1.375,
                    y_coord,
                    text="₩",
                    angle=180,
                    font=("courier", (self.board_side - 2) // 49),
                )
                canvas.create_text(
                    canvas.winfo_width() - 35,
                    y_coord,
                    anchor="e",
                    text=str(j),
                    font=("times", (self.board_side - 2) // 49),
                )
            elif row_counter == 7:  # build house
                canvas.create_text(
                    45,
                    y_coord,
                    anchor="w",
                    text=i,
                    font=("times", (self.board_side - 2) // 49),
                    fill="green",
                )
                canvas.create_text(
                    canvas.winfo_width() / 1.375,
                    y_coord,
                    text="₩",
                    angle=180,
                    font=("courier", (self.board_side - 2) // 49),
                    fill="green",
                )
                canvas.create_text(
                    canvas.winfo_width() - 35,
                    y_coord,
                    anchor="e",
                    text=str(j),
                    font=("times", (self.board_side - 2) // 49),
                    fill="green",
                )
            elif row_counter == 8:  # build hotel
                canvas.create_text(
                    45,
                    y_coord,
                    anchor="w",
                    text=i,
                    font=("times", (self.board_side - 2) // 49),
                    fill="red",
                )
                canvas.create_text(
                    canvas.winfo_width() / 1.375,
                    y_coord,
                    text="₩",
                    angle=180,
                    font=("courier", (self.board_side - 2) // 49),
                    fill="red",
                )
                canvas.create_text(
                    canvas.winfo_width() - 35,
                    y_coord,
                    anchor="e",
                    text=str(j),
                    font=("times", (self.board_side - 2) // 49),
                    fill="red",
                )

            y_coord += canvas.winfo_height() / 11

    def property_frame_popup(self, position):
        position %= 40
        if self.property_frame.winfo_exists():
            self.property_frame.destroy()
        self.property_pos_displayed = position
        self.property_frame = tk.Frame(
            self.main_frame,
            bg="#F9FBFF",
            highlightthickness=2,
            highlightbackground="black",
        )

        self.property_frame.place(
            relx=1, rely=1, relheight=0.575, relwidth=0.475, anchor="se"
        )

        if position in [5, 15, 25, 35]:
            self.station_property_frame(position)
        elif position in [12, 28]:
            self.utility_property_frame(position)
        else:
            self.colour_property_frame(position)

        if self.properties[position].isMortgaged:

            def dest():
                lbl.destroy()
                but.destroy()

            lbl = tk.Label(
                self.property_frame,
                text="MORTGAGED\nPROPERTY",
                bg="#F9FBFF",
                fg="red",
                font=("times", (self.board_side - 2) // 30),
            )
            but = tk.Button(
                self.property_frame,
                text="✕",
                font=("courier", (self.board_side - 2) // 60),
                fg="red",
                activeforeground="red",
                bg="#F9FBFF",
                highlightthickness=0,
                border=0,
                activebackground="#F9FBFF",
                command=dest,
            )
            if position in [5, 15, 25, 35, 12, 28]:
                lbl.place(
                    relx=0.5, rely=0.7, relheight=0.35, relwidth=1, anchor="center"
                )
                but.place(relx=0.875, rely=0.525, anchor="ne")
            else:
                lbl.place(
                    relx=0.5, rely=0.53, relheight=0.4225, relwidth=1, anchor="center"
                )
                but.place(relx=0.875, rely=0.3175, anchor="ne")

    # endregion

    # region # Player Frame

    def player_frame_popup(self, list_of_open=[]):
        self.player_frame = tk.Frame(self.main_frame)

        self.player_frame.place(
            relx=0, rely=0.999, relheight=0.575, relwidth=0.5, anchor="sw"
        )

        scroll = ttk.Scrollbar(self.player_frame, orient="vertical")
        scroll.place(relx=1, rely=0, relwidth=0.06, anchor="ne", relheight=1)

        self.player_tree = ttk.Treeview(
            self.player_frame, columns=("Player", "Value"), yscrollcommand=scroll.set
        )

        scroll.configure(command=self.player_tree.yview)

        self.player_tree.column(
            "#0",
            width=10,
        )
        self.player_tree.column(
            "Player",
            width=int((self.board_side - 2) // 4.25) - 10,
            anchor="center",
            minwidth=int((self.board_side - 2) // 4.7),
        )
        self.player_tree.column(
            "Value",
            width=int((self.board_side - 2) // 4.25) - 10,
            anchor="center",
            minwidth=int((self.board_side - 2) // 4.7),
        )
        self.player_tree.heading("#0", text="")
        self.player_tree.heading("Player", text="Player → Properties", anchor="center")
        self.player_tree.heading("Value", text="Cash → Value", anchor="center")

        for i, j in self.player_details.items():
            self.player_tree.insert(
                parent="",
                index="end",
                iid=i,
                text="",
                values=(j["Name"], j["Money"]),
                tags=j["Colour"],
            )
            self.player_tree.tag_configure(j["Colour"], foreground=j["Colour"])

            if i in list_of_open:
                self.player_tree.item(i, open=True)
            count = 0
            for k in j["Properties"]:
                try:
                    self.player_tree.insert(
                        parent=i,
                        index="end",
                        iid=k.position,
                        text="",
                        values=(k.name, k.value()),
                        tag=k.hex,
                    )
                except:
                    self.player_tree.insert(
                        parent=i,
                        index="end",
                        iid=k.position,
                        text="",
                        values=(k.name, k.value()),
                    )
                count += 1

            if j["GOJF"]:
                self.player_tree.insert(
                    parent=i,
                    index="end",
                    iid="gojf" + i,
                    text="",
                    values=(
                        "Get out of Jail Free" + ("s" if j["GOJF"] > 1 else ""),
                        j["GOJF"],
                    ),
                )

        for i in self.properties.values():
            try:
                self.player_tree.tag_configure(i.hex, background=i.hex)
            except:
                pass

        self.player_tree.place(relx=0, rely=0.5, anchor="w", relheight=1, relwidth=0.94)
        self.player_tree.bind(
            "<<TreeviewSelect>>", lambda event: self.treeview_click(event)
        )

    def treeview_click(self, event):
        try:
            self.property_frame_popup(int(self.player_tree.focus()))
        except:
            pass

    def open_children(self, colour):
        for i in self.player_tree.selection():
            self.player_tree.selection_remove(i)
        for i in self.player_details:
            if self.player_tree.item(i, "open"):
                self.player_tree.item(i, open=False)

        for i, j in self.player_details.items():
            if j["Colour"] == colour:
                self.player_tree.item(i, open=True)
                self.player_tree.selection_set(i)

    # endregion

    def action_frame_popup(self, txt):
        self.action_frame = tk.Frame(
            self.main_frame,
        )
        self.action_frame.place(relx=0, rely=0, relwidth=1, relheight=0.4, anchor="nw")

        if self.me not in self.uuids:
            self.roll_button.configure(state="disabled")
            tk.Label(
                self.action_frame,
                text=f"You are bankrupt!\n\n{self.player_details[self.turn]['Name']} is playing!",
                font=50,
            ).place(relx=0.5, rely=0.5, anchor="center")

        else:

            if self.turn != self.me:
                self.roll_button.configure(state="disabled")
                not_your_turn = tk.Label(
                    self.action_frame,
                    text=f'{self.player_details[self.turn]["Name"]} is playing!',
                    font=50,
                )
                not_your_turn.place(relx=0.5, rely=0.5, anchor="center")

            else:
                self.buy_button = ttk.Button(
                    self.action_frame,
                    text="BUY",
                    style="16.TButton",
                    command=lambda: self.buy_property(
                        self.player_details[self.turn]["Position"] % 40, self.turn
                    ),
                )
                self.buy_button.place(relx=0.2, rely=0.1, anchor="center")

                self.build_button = ttk.Button(
                    self.action_frame,
                    text="BUILD",
                    style="16.TButton",
                    command=self.build_sell_action_frame,
                )
                self.build_button.place(relx=0.2, rely=0.3, anchor="center")

                self.trade_button = ttk.Button(
                    self.action_frame,
                    text="TRADE",
                    style="16.TButton",
                    command=self.trade,
                )
                self.trade_button.place(relx=0.2, rely=0.5, anchor="center")

                self.mortgage_button = ttk.Button(
                    self.action_frame,
                    text="MORTGAGE",
                    style="16.TButton",
                    command=lambda: self.mortgage_unmortgage(True),
                )
                self.mortgage_button.place(relx=0.8, rely=0.1, anchor="center")

                self.unmortgage_button = ttk.Button(
                    self.action_frame,
                    text="UNMORTGAGE",
                    style="13.TButton",
                    command=lambda: self.mortgage_unmortgage(False),
                )
                self.unmortgage_button.place(relx=0.8, rely=0.3, anchor="center")

                self.sell_button = ttk.Button(
                    self.action_frame,
                    text="SELL HOUSES",
                    style="14.TButton",
                    command=lambda: self.build_sell_action_frame(sell=True),
                )
                self.sell_button.place(relx=0.8, rely=0.5, anchor="center")

                self.end_button = ttk.Button(
                    self.action_frame,
                    text="END TURN",
                    style="16.TButton",
                    command=lambda: self.end_turn(),
                )
                self.end_button.place(relx=0.5, rely=0.3, anchor="center")

                self.current_txt = txt
                action_label = tk.Label(
                    self.action_frame, text=self.current_txt, font=30
                )
                action_label.place(relx=0.5, rely=0.75, anchor="center")

                self.toggle_action_buttons(True)

    # region # Mortgage, Unmortgage

    def mortgage_unmortgage(self, mortgage):
        self.timer.reset()
        self.mortgage_frame = tk.Frame(
            self.action_frame,
        )
        self.mortgage_frame.place(
            relx=0.5, rely=0.5, relwidth=1, relheight=1, anchor="center"
        )

        tk.Button(
            self.mortgage_frame,
            text="← BACK",
            font=("times", (self.board_side - 2) // 60),
            highlightthickness=0,
            activebackground=self.mortgage_frame.cget("bg"),
            border=0,
            command=self.mortgage_frame.destroy,
        ).place(relx=0.1, rely=0.05, anchor="ne")

        self.bind("<Escape>", lambda a: self.mortgage_frame.destroy())

        tk.Label(
            self.mortgage_frame,
            text=f"Select the properties that you wish to {'Mortgage' if mortgage else 'Unmortgage'}:",
            font=("times", (self.board_side - 2) // 50),
        ).place(relx=0.5, rely=0.05, anchor="n")

        self.list_frame = tk.Frame(self.mortgage_frame)
        self.list_frame.place(
            relx=0.5, rely=0.15, relwidth=1, relheight=0.6, anchor="n"
        )

        def update_mortgage():
            try:
                self.mortgage_label.destroy()
            except:
                pass
            self.mortvalue = 0
            if mortgage:
                for i, j in self.mortgage_var.items():
                    if j.get():
                        self.mortvalue += i.mortgage

                txt = f"Total Mortgage Value: {self.mortvalue}"

            else:
                for i, j in self.mortgage_var.items():
                    if j.get():
                        self.mortvalue += int(1.1 * i.mortgage)

                txt = f"Total Cost to Unmortgage: {self.mortvalue}"
            self.mortgage_label = tk.Label(
                self.mortgage_frame,
                text=txt,
                font=("times", (self.board_side - 2) // 50),
            )
            self.mortgage_label.place(relx=0.3, rely=0.85, anchor="center")
            self.mortgage_list = []
            for i, j in self.mortgage_var.items():
                if j.get():
                    self.mortgage_list.append(i.position)

        l = []
        for i in self.player_details[self.turn]["Properties"]:
            if mortgage:
                if not i.isMortgaged and i.houses <= 0:
                    l.append(i)
            else:
                if i.isMortgaged:
                    l.append(i)

        self.mortgage_var = {}
        self.mortgage_checkboxes = {}
        for i in l:
            self.mortgage_var[i] = tk.BooleanVar()
            self.mortgage_checkboxes[i] = tk.Checkbutton(
                self.list_frame,
                text=i.name,
                variable=self.mortgage_var[i],
                offvalue=False,
                onvalue=True,
                command=update_mortgage,
                selectcolor=self.list_frame.cget("bg"),
                activebackground=self.list_frame.cget("bg"),
            )
            if i.hex:
                self.mortgage_checkboxes[i].configure(fg=i.hex)
        x = y = 0
        k = 1
        for i in self.mortgage_checkboxes.values():
            i.place(relx=x, rely=y, anchor="nw")
            if k % 4:
                x += 0.25
            else:
                y += 1 / 7.25
                x = 0
            k += 1

        def clear_mort():
            for i in self.mortgage_checkboxes.values():
                i.deselect()
            try:
                self.mortgage_label.destroy()
            except:
                pass

        self.final_mortgage_button = ttk.Button(
            self.mortgage_frame,
            text="MORTGAGE" if mortgage else "UNMORTGAGE",
            style=f"{(self.board_side - 2) // 60}.TButton",
            command=lambda: self.final_mortgage(mortgage, self.mortgage_list),
        )
        self.final_mortgage_button.place(relx=0.65, rely=0.875, anchor="nw")

        self.clear_mort_button = ttk.Button(
            self.mortgage_frame,
            text="CLEAR",
            style=f"{(self.board_side - 2) // 60}.TButton",
            command=clear_mort,
        )
        self.clear_mort_button.place(relx=0.825, rely=0.875, anchor="nw")

    def final_mortgage(self, mortgage, l, received=False):
        try:
            self.final_mortgage_button.configure(state="disabled")
            self.clear_mort_button.configure(state="disabled")
        except:
            pass
        if not received:
            if self.show_message(
                "Mortgage Properties?" if mortgage else "Unmortgage Properties",
                f"Are you sure you wish to mortgage the selected properties to receive {self.mortvalue}?"
                if mortgage
                else f"Are you sure you wish to unmortgage the selected properties for {self.mortvalue}?"
                + (
                    "\n*This will leave you in debt to the bank, forcing you to Mortgage or Sell Houses! Proceed with Caution!"
                    if self.player_details[self.turn]["Money"] - self.mortvalue < 0
                    else ""
                ),
                type="okcancel",
            ):
                pass
            else:
                try:
                    self.final_mortgage_button.configure(state="disabled")
                    self.clear_mort_button.configure(state="disabled")
                except:
                    pass
                if not self.isInDebt:
                    self.update_game()
                return
        self.mortvalue = 0
        for i in l:
            self.properties[i].isMortgaged = mortgage
            self.mortvalue += (
                self.properties[i].mortgage
                if mortgage
                else int(1.1 * self.properties[i].mortgage)
            )
        self.update_game()
        self.pay(self.turn, -self.mortvalue if mortgage else self.mortvalue)
        if not received:
            self.send_msg(("MORTGAGE", mortgage, l))
        if self.isInDebt:
            payer, amt, receiver = self.debt_details
            self.pay(payer, amt, receiver)

    # endregion

    # region # Build, Sell

    def find_my_sets(self, sell=False):
        my_sets = []
        for i in self.player_details[self.turn]["Properties"]:
            if (
                i.houses >= 0
                and i.colour not in my_sets
                and i.colour not in ["Station", "Utility"]
            ):
                my_sets.append(i.colour)
        if not sell:
            for i in self.player_details[self.turn]["Properties"]:
                if i.isMortgaged and i.colour in my_sets:
                    my_sets.remove(i.colour)

        return my_sets

    def build_sell_action_frame(self, sell=False):
        self.timer.reset()
        self.build_frame = tk.Frame(self.action_frame)
        self.build_frame.place(relx=0, rely=0, relheight=1, relwidth=1, anchor="nw")

        tk.Button(
            self.build_frame,
            text="← BACK",
            font=("times", (self.board_side - 2) // 60),
            highlightthickness=0,
            border=0,
            activebackground=self.build_frame.cget("bg"),
            command=self.build_frame.destroy,
        ).place(relx=0.1, rely=0.05, anchor="ne")

        self.bind("<Escape>", lambda a: self.build_frame.destroy())

        my_sets = self.find_my_sets(sell)
        tk.Label(
            self.build_frame,
            text="Select the Colour Set: ",
            font=("times", (self.board_side - 2) // 50),
        ).place(relx=0.1, rely=0.2, anchor="nw")
        self.select_set = ttk.Combobox(self.build_frame, value=my_sets, width=15)
        self.select_set.place(relx=0.5, rely=0.2, anchor="nw")

        def distribute_build(event, set_properties):
            try:
                self.extrahouse_label.destroy()
                for i in self.radio_dict.values():
                    i.destroy()
            except:
                pass
            try:
                self.extrahouse_label.destroy()
                for i in self.checkbuttons_dict.values():
                    i.destroy()
            except:
                pass
            try:
                self.clear_build_button.destroy()
                self.final_build_button.destroy()
            except:
                pass

            total_houses = int(self.select_houses.get())
            no_of_properties = len(set_properties.values())
            old_houses = list(set_properties.values())
            plot = [(i, old_houses[i]) for i in range(len(old_houses))]
            if (
                no_of_properties == 3
                and sum(old_houses) % 3 == (2 if sell else 1)
                and total_houses == 1
            ):
                plot = sorted(plot, key=lambda x: x[-1])
                a = 1 if sell else 0
                b = a + 1
                self.new_building = [
                    0,
                    0,
                    0,
                    (-1 if sell else 1),
                    (plot[a][0], plot[b][0]),
                ]
            else:
                base = (
                    sum(old_houses) + total_houses * (-1 if sell else 1)
                ) // no_of_properties
                self.new_building = (
                    [base - i for i in old_houses]
                    + [
                        (sum(old_houses) + total_houses * (-1 if sell else 1))
                        % no_of_properties
                    ]
                    + [tuple(range(0, len(old_houses)))]
                )
            new_before_extra = copy.deepcopy(self.new_building)

            def final_text_func():
                d = {
                    0: "0 Houses",
                    1: "1 House",
                    2: "2 Houses",
                    3: "3 Houses",
                    4: "4 Houses",
                    5: "A Hotel",
                }
                finaltxt = f"After {'Selling' if sell else 'Buying'}, You will have"
                for i in range(len(self.new_building[:-2])):
                    finaltxt += f"\n→{d[old_houses[i]+self.new_building[i]]} on {list(set_properties.keys())[i].name}"
                finaltxt += f"\n {'receiving' if sell else 'on paying'} {int(list(set_properties.keys())[0].build * total_houses * (0.5 if sell else 1))}"
                try:
                    self.final_build_txt_label.destroy()
                except:
                    pass
                self.final_build_txt_label = tk.Label(
                    self.build_frame,
                    text=finaltxt,
                    font=("times", (self.board_side - 2) // 50),
                )
                self.final_build_txt_label.place(relx=0.5, rely=0.475, anchor="nw")

            def extrahouse_clicked(val, opposite):
                if sell:
                    if sum(self.new_building[:-2]) <= total_houses:
                        self.new_building = copy.deepcopy(new_before_extra)
                else:
                    if sum(self.new_building[:-2]) >= total_houses:
                        self.new_building = copy.deepcopy(new_before_extra)
                if opposite:
                    for i in range(len(self.new_building[:-2])):
                        if i != val:
                            self.new_building[i] += self.new_building[-2] // 2
                else:
                    self.new_building[val] += self.new_building[-2]

                final_text_func()

            l = []

            def check(prop):
                if prop in l:
                    l.remove(prop)
                else:
                    l.append(prop)
                if len(l) == 3:
                    self.checkbuttons_vals[l[0]].set(True)
                    self.checkbuttons_dict[l[0]].deselect()
                    l.remove(l[0])
                    try:
                        self.final_build_button.configure(state="normal")
                    except:
                        pass
                    for i in list(self.checkbuttons_vals.keys()):
                        if i not in l:
                            self.extrahouse.set(
                                list(self.checkbuttons_vals.keys()).index(i)
                            )
                    extrahouse_clicked(self.extrahouse.get(), opp)
                elif len(l) == 1:
                    try:
                        self.final_build_button.configure(state="disabled")
                    except:
                        pass
                elif len(l) == 2:
                    try:
                        self.final_build_button.configure(state="normal")
                    except:
                        pass
                    for i in list(self.checkbuttons_vals.keys()):
                        if i not in l:
                            self.extrahouse.set(
                                list(self.checkbuttons_vals.keys()).index(i)
                            )
                    extrahouse_clicked(self.extrahouse.get(), opp)

            if self.new_building[-2]:
                self.extrahouse = tk.IntVar()
                extrahouse_txt = f"{'Keep' if sell else 'Build'} Extra House on?"
                if self.new_building[-2] == 1:
                    self.extrahouse.set(self.new_building[-1][-1])
                    opp = False
                elif self.new_building[-2] == -1:
                    self.extrahouse.set(self.new_building[-1][0])
                    extrahouse_txt = f"Sell House From?"
                    opp = False
                elif self.new_building[-2] in [2, -2]:
                    extrahouse_txt = f"{'Keep' if sell else 'Build'} Extra Houses on?"
                    opp = True
                self.extrahouse_label = tk.Label(
                    self.build_frame,
                    text=extrahouse_txt,
                    font=("times", (self.board_side - 2) // 50),
                )
                self.extrahouse_label.place(relx=0.1, rely=0.5, anchor="nw")

                extrahouse_clicked(self.extrahouse.get(), opp)
                if opp:
                    self.checkbuttons_vals = {}
                    self.checkbuttons_dict = {}
                    try:
                        self.final_build_button.configure(state="disabled")
                    except:
                        pass
                    k = 0
                    for i in set_properties:
                        self.checkbuttons_vals[i.name] = tk.BooleanVar(value=True)
                        self.checkbuttons_dict[i.name] = tk.Checkbutton(
                            self.build_frame,
                            text=i.name,
                            variable=self.checkbuttons_vals[i.name],
                            onvalue=False,
                            offvalue=True,
                            fg=i.hex,
                            command=lambda i=i: check(i.name),
                            selectcolor=self.build_frame.cget("bg"),
                            activebackground=self.build_frame.cget("bg"),
                        )
                        self.checkbuttons_dict[i.name].invoke()
                        self.checkbuttons_dict[i.name].place(
                            relx=0.1, rely=0.6 + (k / 10), anchor="nw"
                        )
                        k += 1
                else:
                    k = 0
                    for i in set_properties:
                        if k in self.new_building[-1]:
                            self.radio_dict[i.name] = ttk.Radiobutton(
                                self.build_frame,
                                text=i.name,
                                variable=self.extrahouse,
                                value=k,
                                command=lambda: extrahouse_clicked(
                                    self.extrahouse.get(), opp
                                ),
                            )
                            self.radio_dict[i.name].place(
                                relx=0.1, rely=0.6 + (k / 10), anchor="nw"
                            )
                        k += 1
            else:
                final_text_func()

            def build_all():
                try:
                    self.final_build_button.configure(state="disabled")
                    self.clear_build_button.configure(state="disabled")
                except:
                    pass
                if sell:
                    conftxt = f"Are you sure you want to sell {total_houses} houses from the {list(set_properties.keys())[0].colour} set, leaving {(self.player_details[self.me]['Money'])+int(list(set_properties.keys())[0].build * total_houses *0.5)} cash with you"
                else:
                    conftxt = f"Are you sure you want to pay {list(set_properties.keys())[0].build * total_houses} to build on the {list(set_properties.keys())[0].colour} set, leaving {(self.player_details[self.me]['Money'])-list(set_properties.keys())[0].build * total_houses} cash with you"

                if self.show_message(
                    f"Confirm {'Sell' if sell else 'Build'}",
                    conftxt,
                    type="okcancel",
                ):
                    for i in range(len(self.new_building[:-2])):
                        self.build_sell(
                            list(set_properties.keys())[i].position,
                            self.new_building[i],
                            sell,
                        )
                else:
                    try:
                        self.final_build_button.configure(state="normal")
                        self.clear_build_button.configure(state="normal")
                    except:
                        pass

            self.final_build_button = ttk.Button(
                self.build_frame,
                text="SELL" if sell else "BUILD",
                style=f"{(self.board_side - 2) // 60}.TButton",
                command=build_all,
            )
            self.final_build_button.place(relx=0.65, rely=0.875, anchor="nw")

            self.clear_build_button = ttk.Button(
                self.build_frame,
                text="CLEAR",
                style=f"{(self.board_side - 2) // 60}.TButton",
                command=lambda: clear_all(True),
            )
            self.clear_build_button.place(relx=0.8, rely=0.875, anchor="nw")

        def clear_all(all):
            try:
                self.select_houses.destroy()
                self.select_houses_label.destroy()
            except:
                pass
            try:
                self.final_build_txt_label.destroy()
            except:
                pass
            try:
                self.clear_build_button.destroy()
                self.final_build_button.destroy()
            except:
                pass
            try:
                self.extrahouse_label.destroy()
                for i in self.radio_dict.values():
                    i.destroy()
            except:
                pass
            try:
                self.extrahouse_label.destroy()
                for i in self.checkbuttons_dict.values():
                    i.destroy()
            except:
                pass
            if all:
                self.select_set.set("")

        def selected(event):
            clear_all(False)
            selected_set = self.select_set.get()
            set_properties = {}
            for i in self.player_details[self.turn]["Properties"]:
                if i.colour == selected_set:
                    set_properties[i] = i.houses
            houses_possible = 0
            if len(set_properties) == 2:
                houses_possible = 10 - sum(set_properties.values())
            else:
                houses_possible = 15 - sum(set_properties.values())

            if (
                list(set_properties.keys())[0].build * houses_possible
                > self.player_details[self.me]["Money"]
            ):
                houses_possible = (
                    self.player_details[self.me]["Money"]
                    // list(set_properties.keys())[0].build
                )

            if sell:
                houses_possible = sum(set_properties.values())

            self.houses_list = list(range(1, houses_possible + 1))
            self.select_houses_label = tk.Label(
                self.build_frame,
                text="Select the Number of Houses: ",
                font=("times", (self.board_side - 2) // 50),
            )
            self.select_houses_label.place(relx=0.1, rely=0.35, anchor="nw")
            self.select_houses = ttk.Combobox(
                self.build_frame, value=self.houses_list, width=15
            )
            self.select_houses.place(relx=0.5, rely=0.35, anchor="nw")

            self.radio_dict = {}
            self.extrahouse_label = None
            self.select_houses.bind(
                "<<ComboboxSelected>>",
                lambda event: distribute_build(event, set_properties),
            )
            self.select_houses.bind(
                "<KeyRelease>", lambda event: search(event, "houses")
            )

        self.select_set.bind("<<ComboboxSelected>>", selected)
        self.select_set.bind("<KeyRelease>", lambda event: search(event, "set"))

        def search(event, combobox):
            value = event.widget.get()
            if combobox == "set":
                if value:
                    data = []
                    for i in my_sets:
                        if value.lower() in i.lower():
                            data.append(i)

                    self.select_set.configure(values=data)
                else:
                    self.select_set.configure(values=my_sets)
            elif combobox == "houses":
                if value:
                    data = []
                    for i in self.houses_list:
                        if value.lower() in str(i):
                            data.append(i)

                    self.select_houses.configure(values=data)
                else:
                    self.select_houses.configure(values=self.houses_list)

    def build_sell(self, property, number, sell=False, received=False):
        if self.properties[property].owner:
            if self.properties[property].houses + number > 5:
                print(f"ERROR! Can't {'sell' if sell else 'build'} more than 5")
            else:
                self.properties[property].houses += number
                self.player_details[self.properties[property].owner]["Money"] -= int(
                    self.properties[property].build * number * (0.5 if sell else 1)
                )
            self.place_houses()
            self.update_game()
        else:
            print("You dont own this property")

        if not received:
            self.send_msg(("BUILD", property, number, sell))
        if self.isInDebt:
            payer, amt, receiver = self.debt_details
            self.pay(payer, amt, receiver)

    def place_houses(self):
        HOUSES = os.path.join(MONOPOLY_ASSETS, "houses")
        d = {
            1: ["house_1", 0.2],
            2: ["house_2", 0.36],
            3: ["house_3", 0.54],
            4: ["house_4", 0.6],
            5: ["hotel", 0.2],
        }
        for i, j in self.properties.items():
            if j.hex:
                if j.houses > 0:
                    x1, y1 = self.position_to_xy(i)
                    size = [d[j.houses][1], 0.2]
                    if i < 10:
                        x = x1 - self.property_width / 2
                        y = y1 + self.property_height * 0.1
                        rotation = "down"
                    elif i < 20:
                        x = x1 - self.property_height * 0.1
                        y = y1 + self.property_width / 2
                        rotation = "left"
                        size = size[::-1]
                    elif i < 30:
                        x = x1 - self.property_width / 2
                        y = y1 + self.property_height * 0.9
                        rotation = "up"
                    else:
                        x = x1 - self.property_height * 0.9
                        y = y1 + self.property_width / 2
                        rotation = "right"
                        size = size[::-1]
                    house_image = ImageTk.PhotoImage(
                        Image.open(
                            os.path.join(HOUSES, f"{d[j.houses][0]}_{rotation}.png")
                        )
                    ).resize(
                        (
                            int((self.property_height) * size[0]),
                            int((self.property_height) * size[1]),
                        ),
                        Image.Resampling.LANCZOS,
                    )

                    self.house_images.append(house_image)
                    self.board_canvas.create_image(x, y, image=self.house_images[-1])

    # endregion

    def buy_property(self, propertypos, buyer, received=False):
        self.timer.reset()
        self.toggle_action_buttons()
        if not received:
            if self.show_message(
                f"Buy {self.properties[propertypos].name}?",
                f"Are you sure you wish to buy {self.properties[propertypos].name} for {self.properties[propertypos].price}?"
                + (
                    "\n*This will leave you in debt to the bank, forcing you to Mortgage or Sell Houses! Proceed with Caution!"
                    if (self.player_details[buyer]["Money"])
                    - self.properties[propertypos].price
                    < 0
                    else ""
                ),
                type="okcancel",
            ):
                self.send_msg(("BUY", propertypos))
            else:
                self.update_game("Buy")
                self.toggle_action_buttons(True)
                return

        if self.properties[propertypos].colour:
            if not self.properties[propertypos].owner:
                self.properties[propertypos].owner = buyer
                l = self.player_details[buyer]["Properties"]
                l.append(self.properties[propertypos])
                self.pay(buyer, self.properties[propertypos].price)
                # Inserting Properties in Sorted order
                l.sort(key=lambda i: i.position)
                for i in range(len(l)):
                    if l[i].colour == "Station":
                        l.append(l.pop(i))
                for i in range(len(l)):
                    if l[i].colour == "Utility":
                        l.append(l.pop(i))

                self.player_details[buyer].update({"Properties": l})
                if self.properties[propertypos].colour in [
                    "Brown",
                    "Dark Blue",
                ]:
                    colour_set = 2
                else:
                    colour_set = 3

                if self.count_colour(propertypos) == colour_set:
                    for i in self.properties.values():
                        if i.colour == self.properties[propertypos].colour:
                            i.houses = 0
            else:
                print("Owned")

        else:
            print("Can't Buy")

        if not self.isInDebt:
            self.update_game("Default")

    # region # Trade

    def exec_trade(self, offeror, offeree, propertyrecv, propertygive, cash):
        for j in self.properties.values():
            if j.name == propertyrecv:
                j.owner = offeror
                l = self.player_details[offeror]["Properties"]
                l.append(j)
                l.sort(key=lambda y: y.position)
                for x in range(len(l)):
                    if l[x].colour == "Station":
                        l.append(l.pop(x))
                for x in range(len(l)):
                    if l[x].colour == "Utility":
                        l.append(l.pop(x))
                self.player_details[offeree]["Properties"].remove(j)
            if j.name == propertygive:
                j.owner = offeree
                l = self.player_details[offeree]["Properties"]
                l.append(j)
                l.sort(key=lambda y: y.position)
                for x in range(len(l)):
                    if l[x].colour == "Station":
                        l.append(l.pop(x))
                for x in range(len(l)):
                    if l[x].colour == "Utility":
                        l.append(l.pop(x))
                self.player_details[offeror]["Properties"].remove(j)
        self.pay(offeree, cash, offeror)
        self.update_game()

    def recv_trade(self, offeror, propertyrecv, propertygive, cash):
        self.collective["TRADE"] = ("RECV", offeror)
        self.recv_trade_frame = tk.Frame(self.action_frame)
        self.recv_trade_frame.place(
            relx=0, rely=0, relwidth=1, relheight=1, anchor="nw"
        )

        tk.Label(
            self.recv_trade_frame,
            text=f"{self.player_details[offeror]['Name']} has offered a Trade:",
            font=("times", (self.board_side - 2) // 50),
        ).place(relx=0.5, rely=0.25, anchor="center")

        p = propertygive
        r = propertyrecv
        finaltxt1 = f"You will receive: " + (p if p else "")
        finaltxt1 += (
            ((" & " if p else "") + str((-cash if cash < 0 else "")))
            if cash < 0
            else ""
        )
        if not (p or cash < 0):
            finaltxt1 += "Nothing"
        finaltxt2 = f"You will give: " + (r if r else "")
        finaltxt2 += (
            ((" & " if r else "") + str((cash if cash > 0 else ""))) if cash > 0 else ""
        )
        if not (r or cash > 0):
            finaltxt2 += "Nothing"

        finaltxt = finaltxt1 + "\n" + finaltxt2

        tk.Label(
            self.recv_trade_frame,
            text=finaltxt,
            font=("times", (self.board_side - 2) // 50),
            justify="left",
        ).place(relx=0.5, rely=0.5, anchor="center")

        ttk.Button(
            self.recv_trade_frame,
            text="YES",
            style="10.TButton",
            command=lambda: reply(
                ("TRADE", "ANSWER", True, offeror, propertyrecv, propertygive, cash)
            ),
        ).place(relx=0.4, rely=0.75, anchor="center")

        ttk.Button(
            self.recv_trade_frame,
            text="NO",
            style="10.TButton",
            command=lambda: reply(
                ("TRADE", "ANSWER", False, offeror, propertyrecv, propertygive, cash)
            ),
        ).place(relx=0.6, rely=0.75, anchor="center")

        def reply(msg):
            self.send_msg(msg)
            del self.collective["TRADE"]
            if msg[2]:
                self.exec_trade(
                    msg[3],
                    self.me,
                    *msg[4:],
                )
            self.update_game()

    def trade(self):
        self.timer.reset()
        self.trade_frame = tk.Frame(self.action_frame)
        self.trade_frame.place(relx=0, rely=0, relwidth=1, relheight=1, anchor="nw")

        tk.Button(
            self.trade_frame,
            text="← BACK",
            font=("times", (self.board_side - 2) // 60),
            highlightthickness=0,
            border=0,
            activebackground=self.trade_frame.cget("bg"),
            command=self.trade_frame.destroy,
        ).place(relx=0.1, rely=0.05, anchor="ne")

        self.bind("<Escape>", lambda a: self.trade_frame.destroy())

        tk.Label(
            self.trade_frame,
            text="Select Player: ",
            font=("times", (self.board_side - 2) // 50),
        ).place(relx=0.5, rely=0.1, anchor="e")
        self.select_user = ttk.Combobox(
            self.trade_frame,
            value=[self.player_details[i]["Name"] for i in self.uuids if i != self.me],
            width=15,
        )
        self.select_user.place(relx=0.5, rely=0.1, anchor="w")

        self.clear_trade_button = ttk.Button(
            self.trade_frame,
            text="CLEAR ALL",
            style=f"{(self.board_side - 2) // 60}.TButton",
            command=lambda: clear_all(True),
        )
        self.clear_trade_button.place(relx=0.8, rely=0.875, anchor="nw")

        def clear_all(all):
            try:
                self.trade_options_frame.destroy()
            except:
                pass
            try:
                self.final_trade_txt_label.destroy()
            except:
                pass
            if all:
                self.select_user.set("")

        def selected(event):
            clear_all(False)
            offeree = None
            for i, j in self.player_details.items():
                if j["Name"] == self.select_user.get():
                    offeree = i
            offeree_properties = [
                k.name
                for k in self.player_details[offeree]["Properties"]
                if k.houses == -1
            ]

            self.select_prop = {}
            self.select_cash = {}

            self.trade_options_frame = tk.Frame(
                self.trade_frame,
                width=(self.board_side - 2) // 1,
                height=(self.board_side - 2) // 3,
            )
            self.trade_options_frame.place(
                relx=0.5, rely=0.5, anchor="center", relheight=0.5, relwidth=0.75
            )

            tk.Label(
                self.trade_options_frame,
                text="Property: ",
                font=("times", (self.board_side - 2) // 50),
            ).grid(row=1, column=0, sticky="e", padx=8, pady=8)

            tk.Label(
                self.trade_options_frame,
                text="Cash Amount: ",
                font=("times", (self.board_side - 2) // 50),
            ).grid(row=2, column=0, sticky="e", padx=8, pady=8)

            def clear_prop(offeree):
                for i in self.select_prop.values():
                    i.set("")
                final_trade(offeree)

            def clear_cash(offeree):
                for i in self.select_cash.values():
                    i.delete(0, "end")
                final_trade(offeree)

            ttk.Button(
                self.trade_options_frame,
                text="CLEAR",
                style=f"{(self.board_side - 2) // 60}.TButton",
                command=lambda: clear_prop(offeree),
            ).grid(row=1, column=3, sticky="nsew", padx=2, pady=8)

            ttk.Button(
                self.trade_options_frame,
                text="CLEAR",
                style=f"{(self.board_side - 2) // 60}.TButton",
                command=lambda: clear_cash(offeree),
            ).grid(row=2, column=3, sticky="nsew", padx=2, pady=8)

            tk.Label(
                self.trade_options_frame,
                text="RECEIVE",
                font=("times", (self.board_side - 2) // 50, "underline"),
            ).grid(row=0, column=1, sticky="nsew", padx=8, pady=8)

            tk.Label(
                self.trade_options_frame,
                text="GIVE",
                font=("times", (self.board_side - 2) // 50, "underline"),
            ).grid(row=0, column=2, sticky="nsew", padx=8, pady=8)

            self.select_prop[offeree] = ttk.Combobox(
                self.trade_options_frame, value=offeree_properties, width=15
            )
            self.select_prop[offeree].grid(
                row=1, column=1, sticky="nsew", padx=8, pady=8
            )

            self.select_prop[self.me] = ttk.Combobox(
                self.trade_options_frame,
                value=[
                    i.name
                    for i in self.player_details[self.me]["Properties"]
                    if i.houses == -1
                ],
                width=15,
            )
            self.select_prop[self.me].grid(
                row=1, column=2, sticky="nsew", padx=8, pady=8
            )

            def only_numeric_input(e, player):

                if e.isdigit():
                    if int(e) <= self.player_details[player]["Money"]:
                        return True
                    else:
                        return False
                elif e == "":
                    return True
                else:
                    return False

            self.select_cash[offeree] = ttk.Entry(
                self.trade_options_frame,
                width=15,
                validate="key",
                validatecommand=(
                    self.register(lambda e: only_numeric_input(e, offeree)),
                    "%P",
                ),
            )
            self.select_cash[offeree].grid(
                row=2, column=1, sticky="nsew", padx=8, pady=8
            )

            self.select_cash[self.me] = ttk.Entry(
                self.trade_options_frame,
                width=15,
                validate="key",
                validatecommand=(
                    self.register(lambda e: only_numeric_input(e, self.me)),
                    "%P",
                ),
            )
            self.select_cash[self.me].grid(
                row=2, column=2, sticky="nsew", padx=8, pady=8
            )

            for i in self.select_cash.values():
                i.bind(
                    "<KeyRelease>",
                    lambda event: final_trade(offeree),
                )
            for i, j in self.select_prop.items():
                j.bind(
                    "<<ComboboxSelected>>",
                    lambda event: final_trade(offeree),
                )
                j.bind("<KeyRelease>", lambda event: search(event, "property", i))

            final_trade(offeree)

            self.final_trade_button = ttk.Button(
                self.trade_frame,
                text="OFFER",
                style=f"{(self.board_side - 2) // 60}.TButton",
                command=lambda: send_trade(offeree, self.p, self.r, self.cash_val),
            )
            self.final_trade_button.place(relx=0.725, rely=0.875, anchor="nw")

        def send_trade(offeree, propertyrecv, propertygive, cash):
            print(offeree, propertyrecv, propertygive, cash)
            if not (propertyrecv or propertygive or cash):
                return
            else:
                self.toggle_action_buttons()
                if self.show_message(
                    "Make Trade Request?",
                    "Are you sure you wish to send this trade offer?",
                    type="yesno",
                ):
                    self.send_msg(
                        ("TRADE", "REQUEST", offeree, propertyrecv, propertygive, cash)
                    )
                    self.collective["TRADE"] = ("SEND", offeree)
                else:
                    self.toggle_action_buttons(True)
                    return

                waiting = tk.Frame(self.trade_frame)
                waiting.place(relx=0, rely=0, relwidth=1, relheight=1, anchor="nw")

                tk.Label(
                    waiting,
                    text="Waiting for Reply...",
                    font=("times", (self.board_side - 2) // 30),
                ).place(relx=0.5, rely=0.5, anchor="center")

        def final_trade(offeree):
            self.p = self.select_prop[offeree].get()
            q = self.select_cash[offeree].get()
            self.r = self.select_prop[self.me].get()
            s = self.select_cash[self.me].get()
            self.cash_val = (int(q) if q else 0) - (int(s) if s else 0)
            finaltxt1 = f"You will receive: " + (self.p if self.p else "")
            finaltxt1 += (
                (
                    (" & " if self.p else "")
                    + str((self.cash_val if self.cash_val > 0 else ""))
                )
                if self.cash_val > 0
                else ""
            )
            if not (self.p or self.cash_val > 0):
                finaltxt1 += "Nothing"
            finaltxt2 = f"You will give: " + (self.r if self.r else "")
            finaltxt2 += (
                (
                    (" & " if self.r else "")
                    + str((-self.cash_val if self.cash_val < 0 else ""))
                )
                if self.cash_val < 0
                else ""
            )
            if not (self.r or self.cash_val < 0):
                finaltxt2 += "Nothing"

            finaltxt = finaltxt1 + "\n" + finaltxt2

            try:
                self.final_trade_txt_label.destroy()
            except:
                pass
            self.final_trade_txt_label = tk.Label(
                self.trade_frame,
                text=finaltxt,
                font=("times", (self.board_side - 2) // 50),
                justify="left",
            )
            self.final_trade_txt_label.place(relx=0.25, rely=0.9, anchor="center")

        self.select_user.bind("<<ComboboxSelected>>", selected)
        self.select_user.bind("<KeyRelease>", lambda event: search(event, "user"))

        def search(event, combobox, player=None):
            value = event.widget.get()
            if combobox == "user":
                if value:
                    data = []
                    for i in [self.player_details[j]["Name"] for j in self.uuids]:
                        if value.lower() in i.lower():
                            data.append(i)

                    self.select_user.configure(values=data)
                else:
                    self.select_user.configure(
                        values=[self.player_details[j]["Name"] for j in self.uuids]
                    )
            elif combobox == "property":
                if value:
                    data = []
                    for i in [
                        j.name
                        for j in self.player_details[player]["Properties"]
                        if j.houses == -1
                    ]:
                        if value.lower() in i.lower():
                            data.append(i)

                    self.select_prop[player].configure(values=data)
                else:
                    self.select_prop[player].configure(
                        values=[
                            j.name
                            for j in self.player_details[player]["Properties"]
                            if j.houses == -1
                        ]
                    )

    # endregion

    def pass_go(self, player):
        self.player_details[player]["Money"] += 200
        self.update_game("You received 200 as salary!")

    def pay(self, payer, amt, receiver=None):
        self.timer.pause()
        rollstate = str(self.roll_button["state"])
        if self.player_details[payer]["Money"] < amt:
            if self.isBankrupt(amt, payer):
                self.player_leave(payer, receiver)
            else:
                self.isInDebt = True
                self.roll_button.configure(state="disabled")
                self.debt_details = (payer, amt, receiver)
                self.update_game(
                    f"You don't have enough money to pay!\nMortgage properties or sell houses worth {amt- self.player_details[payer]['Money']}"
                )
                d = {
                    "end": self.end_button,
                    "buy": self.buy_button,
                    "build": self.build_button,
                    "trade": self.trade_button,
                    "unmortgage": self.unmortgage_button,
                }
                for i in d:
                    if d[i].winfo_exists():
                        try:
                            d[i].configure(state="disabled")
                        except:
                            pass

        else:
            if amt > 0:
                self.isInDebt = False
                self.roll_button.configure(state=rollstate)
            self.player_details[payer]["Money"] -= amt
            if receiver:
                self.player_details[receiver]["Money"] += amt
            if self.isInDebt:
                payer, amt, receiver = self.debt_details
                self.pay(payer, amt, receiver)
            if amt > 0:
                self.update_game(
                    f"{self.player_details[payer]['Name']} paid {amt} to {self.player_details[receiver]['Name'] if receiver else 'The Bank'}"
                )
            else:
                self.update_game(
                    f"{self.player_details[payer]['Name']} received {-amt} from {self.player_details[receiver]['Name'] if receiver else 'The Bank'}"
                )
            self.toggle_action_buttons(True)
            self.timer.resume()

    # region # End Game

    def quit_game(self):
        if __name__ == "__main__":
            self.http.logout()
            for file in os.scandir(os.path.join(HOME_ASSETS, "cached_pfp")):
                os.remove(file.path)
            root.quit()
        else:
            self.destroy()
        try:
            self.back_to_arcade()
        except:
            pass

    def post_leave(self, usr):
        if "endgame" in self.collective:
            if usr in self.collective["endgame"]:
                self.poll(usr, ("UPDATE", "endgame", -1))

        if "TRADE" in self.collective:
            if self.collective["TRADE"][0] == "SEND":
                self.update_game(
                    "Your trade offer has been declined as the offeree left"
                )
            else:
                self.update_game("Offeror has left")
            del self.collective["TRADE"]

        if self.isInDebt:
            payer, amt, receiver = self.debt_details
            self.player_details[receiver]["Money"] += amt

    def player_leave(self, player_id, debtee=None, quitting=False, inactive=False):
        name = self.player_details[player_id]["Name"]
        if self.turn == player_id:
            self.end_turn(force=True)
        watch = False
        if quitting:
            if self.show_message(
                "Quit Game?",
                "Are you sure you wish to leave this game? This will imply you are forfeiting and will be bankrupt!",
                type="okcancel",
            ):
                self.send_leave("Forfeit")
                if len(self.player_details) == 2:
                    self.end_game(
                        winner=[i for i in self.player_details if i != player_id][0]
                    )
                    return
            else:
                return
        else:
            if len(self.player_details) == 2:
                self.end_game(
                    winner=[i for i in self.player_details if i != player_id][0]
                )
                return
        if self.me == player_id:
            if not quitting and not inactive:
                self.poll(self.me, ("CREATE", "endgame", True, name))
                if self.show_message(
                    "You are bankrupt!",
                    "Unfortunately, you have lost this game, Do you want to watch the other players play?",
                    type="yesno",
                ):
                    watch = True
            else:
                if inactive:
                    self.show_message(
                        "Inactive!",
                        "You have been removed from the game due to inactivity!",
                    )
                    self.send_leave("Inactive")
                else:
                    self.send_leave("Bankrupt")

        for i in self.player_details[player_id]["Properties"]:
            i.owner = debtee
            if debtee:
                l = self.player_details[debtee]["Properties"]
                l.append(i)
                l.sort(key=lambda i: i.position)
                for i in range(len(l)):
                    if l[i].colour == "Station":
                        l.append(l.pop(i))
                for i in range(len(l)):
                    if l[i].colour == "Utility":
                        l.append(l.pop(i))
            else:
                i.houses = -1
                i.isMortgaged = False
        if debtee:
            self.player_details[debtee]["Money"] += self.player_details[player_id][
                "Money"
            ]

        d = {
            "red": self.red_token,
            "green": self.green_token,
            "blue": self.blue_token,
            "gold": self.yellow_token,
        }

        d[self.player_details[player_id]["Colour"]].destroy()
        self.dead_player_details.update({player_id: self.player_details[player_id]})
        del self.player_details[player_id]
        self.uuids.remove(player_id)

        if self.me == player_id:
            if watch:

                def exit_spec():
                    self.send_leave("Spectator")
                    self.quit_game()

                self.protocol("WM_DELETE_WINDOW", exit_spec)
                self.quit_button.configure(command=exit_spec)
                self.end_game_button.destroy()
            else:
                self.quit_game()

        self.update_game(playerleft=name)

    def poll(self, user, poll, received=False):
        if poll[0] == "UPDATE":
            inst, thing, res = poll
            if res == -1:
                del self.collective[thing][user]
            else:
                self.collective[thing][user] = res

            if len(self.collective[thing]) == len(self.player_details):
                c = 0
                for i in self.collective[thing].values():
                    if i:
                        c += 1
                if c > len(self.player_details) // 2:
                    if self.turn == self.me:
                        self.send_msg(("GAME_ENDED",))
                        self.end_game()
                else:
                    self.update_game(
                        "The Majority of players wish to continue the game!"
                    )
                    if self.turn == self.me:
                        self.roll_button.configure(state="normal")
                    self.isEnding = False
                del self.collective[thing]

            if not received:
                self.send_msg(("POLL", ("UPDATE", "endgame", res)))

        elif poll[0] == "CREATE":
            inst, thing, bankr, name = poll
            if bankr:
                self.collective[thing] = {}
                self.get_input(bankr, name)
            else:
                self.collective[thing] = {user: True}
                self.get_input(bankr, name)
            if not received:
                self.send_msg(("POLL", ("CREATE", "endgame", bankr, name)))

    def get_input(self, bankrupt, ender):
        self.isEnding = True
        self.roll_button.configure(state="disabled")
        self.endgame_frame = tk.Frame(self.action_frame)
        self.endgame_frame.place(
            relx=0.5, rely=0.5, relwidth=1, relheight=1, anchor="center"
        )
        if ender == self.player_details[self.me]["Name"]:
            self.waiting_frame = tk.Frame(self.endgame_frame)
            self.waiting_frame.place(
                relx=0.5, rely=0.5, relwidth=1, relheight=1, anchor="center"
            )
            tk.Label(
                self.waiting_frame,
                text="Waiting for others to vote!",
                font=20,
            ).place(relx=0.5, rely=0.5, anchor="center")
        else:
            if bankrupt:
                tk.Label(
                    self.endgame_frame,
                    text=f"{ender} is Bankrupt! Do you want to end the game now?",
                    font=20,
                ).place(relx=0.5, rely=0.5, anchor="center")
            else:
                tk.Label(
                    self.endgame_frame,
                    text=f"{ender} wants to end the game! Do you want to end the game too?",
                    font=20,
                ).place(relx=0.5, rely=0.5, anchor="center")

            def ans(bool):
                self.waiting_frame = tk.Frame(self.endgame_frame)
                self.waiting_frame.place(
                    relx=0.5, rely=0.5, relwidth=1, relheight=1, anchor="center"
                )
                tk.Label(
                    self.waiting_frame,
                    text="Waiting for others to vote!",
                    font=20,
                ).place(relx=0.5, rely=0.5, anchor="center")

                self.poll(self.me, ("UPDATE", "endgame", bool))

            ttk.Button(
                self.endgame_frame,
                text="YES",
                style="16.TButton",
                command=lambda: ans(True),
            ).place(relx=0.4, rely=0.75, anchor="center")

            ttk.Button(
                self.endgame_frame,
                text="NO",
                style="16.TButton",
                command=lambda: ans(False),
            ).place(relx=0.6, rely=0.75, anchor="center")

    def end_game(self, winner=None):
        self.isEnded = True
        self.player_details.update(self.dead_player_details)
        for i in self.player_details.values():
            s = 0
            s += i["Money"]
            for k in i["Properties"]:
                s += k.value
            s += i["GOJF"] * 50
            i.update({"NETWORTH": s})

        winners = [
            (
                max(
                    self.player_details,
                    key=lambda a: self.player_details[a]["NETWORTH"],
                )
                if not winner
                else winner
            )
        ]
        if not winner:
            for i, j in self.player_details.items():
                if j["NETWORTH"] == self.player_details[winners[0]]["NETWORTH"]:
                    if i not in winners and i in self.uuids:
                        winners.append(i)

        def q():
            self.send_leave("ENDED")
            self.quit_game()

        self.protocol("WM_DELETE_WINDOW", q)
        self.roll_button.configure(state="disabled")

        self.final_frame = tk.Frame(self.action_frame)
        self.final_frame.place(
            relx=0.5, rely=0.5, relwidth=1, relheight=1, anchor="center"
        )

        if len(winners) == 1:
            txt = (
                f"{self.player_details[winner]['Name']} has"
                if winner != self.me
                else "You have"
            ) + " won the game!"
        else:
            winners_list = ""
            for i in range(len(winners)):
                winners_list += (
                    self.player_details[winners[i]]["Name"]
                    if winners[i] != self.me
                    else "You"
                )
                if len(winners) - i == 2:
                    winners_list += " & "
                elif len(winners) - i == 1:
                    pass
                else:
                    winners_list += ", "
            winners_list = winners_list.strip()

            txt = f"The winners of the game are: {winners_list}"
        txt += "\n\nNetworths:"
        for i in sorted(
            self.player_details,
            key=lambda a: self.player_details[a]["NETWORTH"],
        ):
            txt += f"\n{self.player_details[i]['Name']} : {self.player_details[i]['NETWORTH']}"
        tk.Label(self.final_frame, text=txt, font=20, justify="center").place(
            relx=0.5, rely=0.05, anchor="n"
        )

        ttk.Button(
            self.final_frame,
            text="EXIT GAME",
            style="20.TButton",
            command=q,
        ).place(relx=0.5, rely=0.8, anchor="center")

        self.result = {
            i["Name"]: {
                "NETWORTH": i["NETWORTH"],
                "PROPERTIES": [j.name for j in i["Properties"]],
                "PLACES": i["PLACES"],
            }
            for i in self.player_details.values()
        }

        if self.me == self.turn:
            Monopoly.http.addgame(
                "MONOPOLY",
                [self.player_details[i]["Name"] for i in winners],
                self.result,
                list(self.result.keys()),
            )

    # endregion

    def CLI(self):
        while True:
            t = tuple(i for i in input().split())
            if t:
                if t[0] == "roll":
                    try:
                        self.roll_dice(roll=(int(t[1]), int(t[2])), cli=True)
                    except:
                        pass
                elif t[0] == "buy":
                    for i in t[1:]:
                        self.buy_property(int(i), self.me)

                elif t[0] == "build":
                    try:
                        self.build_sell(int(t[1]), int(t[2]))
                    except:
                        pass
                else:
                    print("die")
            else:
                print("Closed CLI Thread")
                break


class Chance:
    def __init__(self, game, order):
        self.game: Monopoly = game
        options = [
            lambda: self.advance_to(0),  # GO
            lambda: self.advance_to(24),  # Trafalgar Square
            lambda: self.advance_to(11),  # Pall Mall
            lambda: self.nearest_prop("UT"),
            lambda: self.nearest_prop("RR"),
            lambda: self.nearest_prop("RR"),
            lambda: self.advance_to(5),  # King Cross
            lambda: self.advance_to(39),  # Mayfair
            lambda: self.bank_transaction(-50),
            lambda: self.bank_transaction(-150),
            lambda: self.bank_transaction(-100),
            lambda: self.bank_transaction(15),
            lambda: self.bank_transaction(20),
            lambda: self.bank_transaction(150),
            lambda: self.bank_transaction(-200),
            lambda: self.game.go_to_jail(self.game.turn),
            self.get_out_of_jail_free,
            self.go_back_3,
            self.general_repairs,
            lambda: self.pay_to_players(50),
        ]
        text = [
            "Advance to GO.",
            "Advance to Trafalgar Square.",
            "Advance to Pall Mall.",
            "Advance to the nearest Utility.\nIf unowned, you may buy it from the Bank.\nIf owned, pay owner rent based on previous roll.",
            "Advance to the nearest Railroad.",
            "Advance to the nearest Railroad.",
            "Take a ride to King's Cross Station.",
            "Advance to Mayfair.",
            "Bank pays you dividend of 50.",
            "Your building loan matures.\nCollect 150.",
            "You have won a crossword competition.\nCollect 100.",
            "Pay speeding fine of 15.",
            "Drunk in charge. Pay 20.",
            "Pay school fees of 150.",
            "Bank Error in your favour.\nReceive 200.",
            "Go to Jail. Go directly to Jail.\nDo not pass GO, do not collect 200.",
            "Get out of Jail Free.\nThis card maybe used only once.",
            "Go Back Three Spaces.",
            "Make general repairs on all your property:\nFor each house pay 25, For each hotel pay 100.",
            "You have been elected Chairman of the Board.\nPay each player 50.",
        ]
        self.options = [options[i] for i in order]
        self.text = [text[i] for i in order]

    def go_back_3(self):
        self.game.move(
            self.game.turn,
            37,
            showmove=False,
            endturn=not bool(self.game.doubles_counter),
        )  # ? Move backward animation

    def nearest_prop(self, stuff):
        turn = self.game.turn
        pos = self.game.player_details[turn]["Position"] % 40
        if stuff == "UT":
            move = (
                (12 - pos) % 40
                if (12 - pos) % 40 < (28 - pos) % 40
                else (28 - pos) % 40
            )
        elif stuff == "RR":
            c = [5, 15, 25, 35]
            l = [(i - pos) % 40 for i in c]
            move = min(l)
        self.game.move(turn, move, endturn=not bool(self.game.doubles_counter))

    def advance_to(self, place):
        uuid = self.game.turn
        players = self.game.player_details
        move = (place - players[uuid]["Position"] % 40) % 40
        self.game.move(uuid, move, endturn=not bool(self.game.doubles_counter))

    def get_out_of_jail_free(self):
        self.game.player_details[self.game.turn]["GOJF"] += 1

    def bank_transaction(self, amt):
        uuid = self.game.turn
        self.game.pay(uuid, amt)

    def general_repairs(self):
        properties = self.game.player_details[self.game.turn]["Properties"]
        house, hotel = 0, 0
        for i in properties:
            if i.houses == 5:
                hotel += 1
            elif i.houses > 0:
                house += i.houses
        self.game.pay(self.game.turn, house * 25 + hotel * 100)

    def pay_to_players(self, amt):
        players = self.game.player_details
        for i in players:
            if i != self.game.turn:
                self.game.pay(self.game.turn, amt, i)

    def add_back(self):
        if self.get_out_of_jail_free not in self.options:
            self.options.append(self.get_out_of_jail_free)
            self.text.append("Get out of Jail Free.\nThis card maybe used only once.")

    def __call__(self):
        self.game.after(1500, self.options[0])
        if self.text[0] == "Get out of Jail Free.\nThis card maybe used only once.":
            self.options.remove(self.options[0])
            self.text.remove(self.text[0])
        else:
            self.options.append(self.options.pop(0))
            self.text.append(self.text.pop(0))
        return self.text[-1]


class Community:
    def __init__(self, game, order):
        self.game: Monopoly = game
        options = [
            lambda: self.advance_to(0),
            lambda: self.bank_transaction(-200),
            lambda: self.bank_transaction(50),
            lambda: self.bank_transaction(-100),
            lambda: self.bank_transaction(-100),
            lambda: self.bank_transaction(-100),
            lambda: self.bank_transaction(-10),
            lambda: self.bank_transaction(-20),
            lambda: self.bank_transaction(-25),
            lambda: self.bank_transaction(-25),
            lambda: self.bank_transaction(50),
            lambda: self.bank_transaction(-50),
            lambda: self.bank_transaction(100),
            lambda: self.pay_to_players(-50),
            lambda: self.pay_to_players(-10),
            lambda: self.game.go_to_jail(self.game.turn),
            self.get_out_of_jail_free,
            self.go_back,
            self.street_repairs,
            lambda: self.bank_transaction(100),
        ]
        text = [
            "Advance to GO.",
            "Bank Error in your favour.\nReceive 200.",
            "Doctor's Fees. Pay 50.",
            "Holiday fund matures. Collect 100.",
            "Life insurance matures. Collect 100.",
            "You inherit 100.",
            "You have won second prize in a beauty contest. Collect 10",
            "Income tax refund. Collect 20.",
            "Receive Consultancy fee of 25.",
            "Receive interest on 7% preference shares: 25",
            "Pay School fees of 50.",
            "From sale of stock you get 50.",
            "Pay Hospital fees of 100.",
            "Grand Opera Opening. Collect 50 from each player.",
            "It's your birthday. Collect 10 from each player.",
            "Go to Jail. Go directly to Jail.\nDo not pass GO, do not collect 200.",
            "Get out of Jail Free.\nThis card maybe used only once.",
            "Go back to Old Kent Road.",
            "You are assessed for street repairs:\nFor each house pay 40, For each hotel pay 115.",
            "Pay your insurance premium worth 100.",
        ]
        self.options = [options[i] for i in order]
        self.text = [text[i] for i in order]

    def go_back(self):
        uuid = self.game.turn
        players = self.game.player_details
        self.game.move(
            self.game.turn,
            (1 - players[uuid]["Position"] % 40) % 40,
            showmove=False,
            endturn=not bool(self.game.doubles_counter),
        )  # ? Move backward animation

    def advance_to(self, place):
        uuid = self.game.turn
        players = self.game.player_details
        move = (place - players[uuid]["Position"] % 40) % 40
        self.game.move(uuid, move, endturn=not bool(self.game.doubles_counter))

    def get_out_of_jail_free(self):
        self.game.player_details[self.game.turn]["GOJF"] += 1

    def bank_transaction(self, amt):
        uuid = self.game.turn
        self.game.pay(uuid, amt)

    def pay_to_players(self, amt):
        players = self.game.player_details
        for i in players:
            if i != self.game.turn:
                self.game.pay(self.game.turn, amt, i)

    def street_repairs(self):
        properties = self.game.player_details[self.game.turn]["Properties"]
        house, hotel = 0, 0
        for i in properties:
            if i.houses == 5:
                hotel += 1
            elif i.houses > 0:
                house += i.houses
        self.game.pay(self.game.turn, house * 40 + hotel * 115)

    def add_back(self):
        if self.get_out_of_jail_free not in self.options:
            self.options.append(self.get_out_of_jail_free)
            self.text.append("Get out of Jail Free.\nThis card maybe used only once.")

    def __call__(self):
        self.game.after(1500, self.options[0])
        if self.text[0] == "Get out of Jail Free.\nThis card maybe used only once.":
            self.options.remove(self.options[0])
            self.text.remove(self.text[0])
        else:
            self.options.append(self.options.pop(0))
            self.text.append(self.text.pop(0))
        return self.text[-1]


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()

    if not os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "wb") as f:
            pickle.dump({"THEME": "dark", "DEFAULT_GAME": 0}, f)
    else:
        with open(SETTINGS_FILE, "rb") as f:
            d = pickle.load(f)
            if d["THEME"] in ["dark", "light"]:
                CURR_THEME = d["THEME"]
            else:
                CURR_THEME = "dark"
                with open(SETTINGS_FILE, "rb+") as f:
                    d = pickle.load(f)
                    d.update({"THEME": "dark"})
                    f.seek(0)
                    pickle.dump(d, f)

    theme.init(root, CURR_THEME)

    try:
        os.mkdir(os.path.join(HOME_ASSETS, "cached_pfp"))
    except:
        pass
    hobj = Http("http://167.71.231.52:5000")
    uname = "user1"
    pwd = "pass1"
    hobj.login(uname, pwd)
    mono = Monopoly(
        {
            "QWERTY": {
                "Name": uname,
                "Colour": "red",
            }
        },
        "QWERTY",
        print,
        hobj,
        order=[[i for i in range(20)], [i for i in range(20)]],
    )
    root.mainloop()
