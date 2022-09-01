import base64
import os
import pickle
import sys
import threading
import tkinter as tk
import tkinter.ttk as ttk
from io import BytesIO
from time import sleep
from tkinter import messagebox as msgb

from PIL import Image, ImageChops, ImageDraw, ImageTk
from plyer import notification as noti

sys.path.append(
    os.path.join(
        os.path.abspath("."), "Client" if "Client" not in os.path.abspath(".") else ""
    )
)

from utilities.http_wrapper import Http
from utilities.rules import Rules
from utilities.theme import Theme
from utilities.timer import Timer

isWin = os.name == "nt"
SETTINGS_FILE = (
    os.path.join(
        os.environ["USERPROFILE"],
        "AppData",
        "Local",
        "Arcade",
        "settings.dat",
    )
    if isWin
    else os.path.join(
        os.environ["HOME"],
        "Applications",
        "Arcade",
        "settings.dat",
    )
)


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


ASSET = resource_path(
    "assets" if os.path.exists("assets") else os.path.join("Client", "assets")
)
HOME_ASSETS = os.path.join(ASSET, "home_assets")
CHESS_ASSETS = os.path.join(ASSET, "chess_assets")


class Chess(tk.Toplevel):
    color = {
        "black": "#eeeed2",
        "white": "#769656",
        "sblack": "#f6f669",
        "swhite": "#baca2b",
        "sbwhite": "#e7edb5",
        "sbblack": "#fcfccb",
        "bwhite": "#cfdac4",
        "bblack": "#f9f9ef",
        "hint": "#d6d6bd",
        "check": "#f33e42",
    }
    size = None
    swap = {"WHITE": "BLACK", "BLACK": "WHITE"}

    def __init__(
        self,
        initialize,
        update,
        http: Http,
        debug=False,
        back=None,
        theme: Theme = None,
    ):
        super().__init__()
        self.theme = theme
        self.me = initialize["ME"]
        self.players = initialize["PLAYERS"]
        self.opponent = [i for i in self.players if i != self.me][0]
        self.side = self.players[self.me]["SIDE"]
        self.time = initialize["TIME"]
        self.add_time = initialize["ADD_TIME"]
        self.back_to_arcade = back
        Chess.http = http

        for i in self.players:
            self.players[i].update(
                {
                    "PFP": Chess.get_pfp(self.players[i]["NAME"], (32, 32)),
                }
            )

        self.board: Board[int, Piece] = Board()
        self.board_ids: dict = {}
        self.imgs: dict = {}
        self.possible_moves: list = []
        self.initialize_gui()
        self.initialize_board()
        self.action_buttons()
        self.selected: int = None
        self.hover: int = None
        self.state: str = "Nothing"
        self.old_selected = None
        self.old_hover = None
        self.COLOREDSQUARES: dict = {"check": None, "move": []}
        self.last_move: list = [-1, -1]
        self.pawn_promotion = None
        self.send = update
        self.turn = "WHITE"
        self.debug = debug
        self.poll = {}
        self.isEnded = False
        self.lock = threading.Lock()
        self.lock.acquire(blocking=False)
        self.place_timers()

    def initialize_gui(self):
        screen_width = int(0.9 * self.winfo_screenwidth())
        screen_height = int(screen_width / 1.9)
        x_coord = self.winfo_screenwidth() // 2 - screen_width // 2
        y_coord = (self.winfo_screenheight() - 70) // 2 - screen_height // 2
        self.geometry(f"{screen_width}x{screen_height}+{x_coord}+{y_coord}")
        self.protocol("WM_DELETE_WINDOW", self.resign)
        self.title("Chess")
        self.iconbitmap(os.path.join(CHESS_ASSETS, "icon.ico"))
        self.canvas = tk.Canvas(self)
        self.canvas.place(relx=0.125, rely=0.5, relheight=0.95, relwidth=1, anchor="w")
        self.canvas.update()
        Chess.size = self.canvas.winfo_height()
        self.minsize(int(Chess.size * 1.75), screen_height)
        self.main_frame = tk.Frame(self)
        self.main_frame.place(
            relx=0.95, rely=0.5, relheight=0.95, relwidth=0.25, anchor="e"
        )

        self.help_img = ImageTk.PhotoImage(
            Image.open(os.path.join(HOME_ASSETS, "help.png")).resize(
                (20, 20),
                Image.Resampling.LANCZOS,
            )
        )

        tk.Button(
            self,
            image=self.help_img,
            highlightthickness=0,
            border=0,
            command=lambda: Rules("Chess"),
        ).place(relx=0.999, rely=0.001, anchor="ne")

        self.disimg = ImageTk.PhotoImage(
            Image.new(
                "RGBA",
                (Chess.size, Chess.size),
                self.winfo_rgb("black") + (int(0.5 * 255),),
            )
        )

        self.disabled_image = self.canvas.create_image(
            Chess.size // 2,
            Chess.size // 2,
            image=self.disimg,
            anchor=tk.CENTER,
        )

        for i in range(8):
            for j in range(8):
                self.imgs[i * 10 + j] = (
                    ImageTk.PhotoImage(
                        Image.open(os.path.join(CHESS_ASSETS, "circle.png")).resize(
                            (Chess.size // (8 * 4), Chess.size // (8 * 4)),
                            Image.Resampling.LANCZOS,
                        ),
                        master=self.canvas,
                    ),
                    ImageTk.PhotoImage(
                        Image.open(os.path.join(CHESS_ASSETS, "circle.png")).resize(
                            (Chess.size // (8), Chess.size // (8)),
                            Image.Resampling.LANCZOS,
                        ),
                        master=self.canvas,
                    ),
                )

        self.enable_canvas()

        self.acc_button = tk.Button(
            self,
            image=self.players[self.me]["PFP"],
            text=f" {self.players[self.me]['NAME']} ▾",
            highlightthickness=0,
            border=0,
            font=("arial black", 14),
            compound="left",
            command=self.account_tab,
        )
        self.acc_button.place(relx=0.01, rely=0.03, anchor="w")
        self.acc_frame = tk.Frame()
        self.acc_frame.destroy()

    # region # Profile Picture

    @staticmethod
    def pfp_make(img):
        b = base64.b64decode(img.encode("latin1"))
        c = Image.open(BytesIO(b))
        return c

    @staticmethod
    def get_pfp(name, resize=(32, 32)):
        if not os.path.isfile(os.path.join(HOME_ASSETS, "cached_pfp", name + ".png")):
            Chess.circle_PIL_Image(Chess.pfp_make(Chess.http.fetch_pfp(name))).save(
                os.path.join(HOME_ASSETS, "cached_pfp", name + ".png")
            )
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

    def account_tab(self):
        if self.acc_frame.winfo_exists():
            self.unbind("<Button-1>")
            self.acc_frame.destroy()
        else:

            def clicked(e):
                if self.acc_frame.winfo_containing(e.x_root, e.y_root) not in [
                    self.quit_button,
                    self.acc_frame,
                    self.acc_button,
                    self.theme_button,
                ]:
                    self.acc_frame.destroy()
                    self.unbind("<Button-1>")

            self.bind("<Button-1>", clicked)
            self.acc_frame = ttk.Frame(self, style="Card.TFrame", padding=4)
            self.acc_frame.place(relx=0.008, rely=0.06, anchor="nw")

            self.quit_button = ttk.Button(
                self.acc_frame, text="QUIT", style="12.TButton", command=self.resign
            )
            if self.isEnded:
                self.quit_button.configure(command=lambda: self.quit_game("ENDED"))
            self.quit_button.grid(row=0, column=0, columnspan=2, sticky="nsew", pady=2)

            theme_var = tk.StringVar(value=self.theme.curr_theme())

            tk.Label(self.acc_frame, text="Dark Mode", font=("rockwell", 12)).grid(
                row=1, column=0, sticky="e", pady=2, padx=6
            )
            self.theme_button = ttk.Checkbutton(
                self.acc_frame,
                style="Switch.TCheckbutton",
                variable=theme_var,
                onvalue="dark",
                offvalue="light",
                command=self.theme.toggle_theme,
            )
            self.theme_button.grid(row=1, column=1, sticky="e", pady=2)

    def initialize_board(self):
        offset = 4
        for i in range(8):
            for j in range(8):
                key = i * 10 + j
                x1, y1, x2, y2 = self.grid_to_coords(i, j)
                color = "white" if (i + j) % 2 else "black"
                base = self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill=Chess.color[color], outline="", state="normal"
                )

                highlight_square = self.canvas.create_rectangle(
                    x1 + offset,
                    y1 + offset,
                    x2 - offset,
                    y2 - offset,
                    fill=Chess.color["b" + color],
                    outline="",
                    state="hidden",
                )

                hint = self.canvas.create_image(
                    (x1 + x2) // 2,
                    (y1 + y2) // 2,
                    image=self.imgs[key][0],
                    anchor=tk.CENTER,
                    state="hidden",
                )

                self.canvas.tag_raise(self.imgs[key])
                self.board_ids[key] = {
                    "base": base,
                    "button": highlight_square,
                    "hint": hint,
                }
        for i in range(8):
            adj = Chess.size // 256
            if self.side == "WHITE":
                x1, y1, a, b = self.grid_to_coords(i)
                x2, y2, a, b = self.grid_to_coords(7 + i * 10)

            else:
                x1, y1, a, b = self.grid_to_coords(i + 70)
                x2, y2, a, b = self.grid_to_coords(i * 10)

            x2, y2 = x2 + Chess.size // 8, y2 + Chess.size // 8
            font = ("Microsoft Sans Serif", 14, "bold")
            self.canvas.create_text(
                x1 + adj,
                y1 + adj,
                text=f"{8-i}",
                anchor=tk.NW,
                fill=f"{Chess.color['black']}"
                if ((8 - i) % 2 if self.side == "WHITE" else not (8 - i) % 2)
                else f"{Chess.color['white']}",
                font=font,
            )
            self.canvas.create_text(
                x2 - adj,
                y2 - adj,
                text=chr(ord("a") + i),
                anchor=tk.SE,
                fill=f"{Chess.color['white']}"
                if ((8 - i) % 2 if self.side == "WHITE" else not (8 - i) % 2)
                else f"{Chess.color['black']}",
                font=font,
            )

        board = self.board.fen["B"]

        for i in range(len(board)):
            for j in range(len(board[i])):
                if board[i][j] != "-":
                    color = "BLACK" if board[i][j].islower() else "WHITE"
                    piece = FEN.pieces[board[i][j].lower()]
                    self.board[j * 10 + i] = ChessPiece(
                        piece, color, self.board, j * 10 + i, self
                    )
                else:
                    self.board[j * 10 + i] = None

    # region # Timers

    def place_timers(self):
        self.timer_labels: dict[str, tk.Label] = {}
        self.timers: dict[str, Timer] = {}
        self.timer_threads: dict[str, threading.Thread] = {}
        self.user_pfp_display: dict[str, tk.Label] = {}

        self.timer_labels[self.me] = tk.Label(self.main_frame, font=("consolas", 45))
        self.timer_labels[self.me].place(relx=0.5, rely=0.875, anchor="center")
        self.timer_threads[self.me] = threading.Thread(
            target=self.timer_init,
            args=(self.me,),
            daemon=True,
        )
        self.user_pfp_display[self.me] = tk.Label(
            self.main_frame,
            image=self.players[self.me]["PFP"],
            text=f" {self.players[self.me]['NAME']}",
            highlightthickness=0,
            border=0,
            font=("rockwell", 16),
            compound="left",
        )
        self.user_pfp_display[self.me].place(relx=0.5, rely=0.775, anchor="center")

        self.timer_labels[self.opponent] = tk.Label(
            self.main_frame, font=("consolas", 45)
        )
        self.timer_labels[self.opponent].place(relx=0.5, rely=0.125, anchor="center")
        self.timer_threads[self.opponent] = threading.Thread(
            target=self.timer_init,
            args=(self.opponent,),
            daemon=True,
        )
        self.user_pfp_display[self.opponent] = tk.Label(
            self.main_frame,
            image=self.players[self.opponent]["PFP"],
            text=f" {self.players[self.opponent]['NAME']}",
            highlightthickness=0,
            border=0,
            font=("rockwell", 16),
            compound="left",
        )
        self.user_pfp_display[self.opponent].place(
            relx=0.5, rely=0.225, anchor="center"
        )

        for i in self.players:
            self.timer_threads[i].start()
            self.timers[i].pause()
            self.timers[i].set_time(self.time)

    def timer_init(self, player, precision="minsec"):
        self.timers[player] = Timer(self.time)
        self.timers[player].start()
        while True:
            if not self.timers[player].is_alive():
                break
            if self.timers[player].time_left() <= 0:
                self.timers[player].stop()
                self.final_frame(
                    "TIME",
                    [i for i in self.players if i != player][0],
                )
                break
            else:
                self.display_timer(
                    self.timers[player], self.timer_labels[player], precision
                )
            sleep(0.09)

    @staticmethod
    def display_timer(timer: Timer, lbl: tk.Label, precision="sec"):
        a = round(timer.time_left(), 2)
        if a < 0.01:
            min, sec, ms = 0, 0, 0
        min, sec, ms = int(a // 60), int(a % 60), int(a * 100 % 100)
        if precision == "sec":
            things = f"{sec:02d}"
        elif precision == "minsec":
            things = f"{min:02d}:{sec:02d}"
        else:
            things += f"{min:02d}:{sec:02d}:{ms:02d}"
        try:
            lbl.configure(text=things)
        except tk.TclError as e:
            print("tcl:", e)

    # endregion

    def action_buttons(self):
        resign = ttk.Button(
            self.main_frame,
            text="Resign",
            style="20.TButton",
            command=self.resign,
        )
        resign.place(relx=0.5, rely=0.4, anchor="center")

        draw = ttk.Button(
            self.main_frame,
            text="Offer Draw",
            style="20.TButton",
            command=self.draw_req,
        )
        draw.place(relx=0.5, rely=0.6, anchor="center")

    def set(self, id: int, state: str, preserve_select=False, overide=False):

        color = "white" if (id // 10 + id % 10) % 2 else "black"

        if id == self.COLOREDSQUARES["check"]:
            return

        if state == "normal":

            if preserve_select and id == self.selected:
                self.set(id, state="select")
                return

            if id not in self.COLOREDSQUARES["move"] or overide:
                color = Chess.color[color]
                self.canvas.itemconfigure(self.board_ids[id]["base"], fill=color)
            else:
                self.canvas.itemconfigure(
                    self.board_ids[id]["base"], fill=Chess.color["s" + color]
                )

            self.canvas.itemconfigure(self.board_ids[id]["button"], state="hidden")

        elif state == "select":
            color = Chess.color["s" + color]
            self.canvas.itemconfigure(self.board_ids[id]["base"], fill=color)

        elif state == "button":

            c1 = "b" + color
            c2 = color

            if id == self.selected or id in self.COLOREDSQUARES["move"]:
                c1 = "s" + c1
                c2 = "s" + c2

            self.canvas.itemconfigure(
                self.board_ids[id]["button"], state="normal", fill=Chess.color[c2]
            )
            self.canvas.itemconfigure(self.board_ids[id]["base"], fill=Chess.color[c1])

        elif state == "check":
            color = Chess.color["check"]
            self.canvas.itemconfigure(self.board_ids[id]["base"], fill=color)

        elif state == "promo":
            self.canvas.itemconfigure(self.board_ids[id]["base"], fill="WHITE")
            self.canvas.tag_raise(self.board_ids[id]["base"])

    def display_moves(self, show: bool = True):
        if show:
            self.possible_moves = self.board.get_moves(self.selected)

            for i in self.possible_moves:
                if self.board[i] != None:

                    self.canvas.itemconfigure(
                        self.board_ids[i]["hint"], image=self.imgs[i][1]
                    )

                self.canvas.itemconfigure(self.board_ids[i]["hint"], state=tk.NORMAL)
        else:
            for i in self.possible_moves:
                self.canvas.itemconfigure(
                    self.board_ids[i]["hint"], image=self.imgs[i][0], state=tk.HIDDEN
                )

            self.possible_moves = []

    def check_for_mate(self, color) -> bool:
        for i in self.board.keys():
            if self.board[i] != None and self.board[i].color == color:
                m = self.board[i].gen_moves(inCheck=True)
                for j in m:
                    b = Board(self.board.fen.value)
                    b.moved(i, j)
                    if not b.is_in_check(color):
                        return False
        return True

    def moveanimation(self, s, e, simul=False):
        x1, y1, x2, y2 = self.grid_to_coords(s)
        x, y = (x1 + x2) // 2, (y1 + y2) // 2
        ex1, ey1, ex2, ey2 = self.grid_to_coords(e)
        x1, y1 = (ex1 + ex2) // 2 - x, (ey1 + ey2) // 2 - y

        t = 0.05
        fps = 80
        n = int(t * fps)
        for i in range(1, n + 1):
            start = int(x + (i / n) * x1)
            end = int(y + (i / n) * y1)
            sleep(t / n)
            self.move_obj(self.board[e], start, end)
        self.oldimg = None
        if not simul:
            self.lock.release()

    def clicked(self, e):
        x, y = self.coords_to_grid(e.x, e.y)
        k = 10 * x + y

        if k in self.possible_moves:
            self.start_move(self.selected, k)
            self.state = "Move"

        elif not self.board[k]:
            pass

        elif self.board[k].color != (self.turn if self.debug else self.side):
            if self.debug:
                # self.state = "PieceSelected"
                pass
        else:
            self.state = "PieceSelected"

        if self.state == "Nothing":
            if self.selected != None:
                self.unselect()
                self.display_moves(False)

        elif self.state == "PieceSelected":
            if self.selected != k:
                if self.selected != None:
                    self.unselect()

                self.selected = k
                if self.side == self.turn or self.debug:
                    self.display_moves()
                    self.set(k, "select")
                    self.set(k, "button")

            self.canvas.tag_raise(self.board[k].img_id)
            self.move_obj(self.board[k], e.x, e.y)

    def released(self, e: tk.Event):
        didMove = False
        if self.state == "Nothing":
            return

        elif self.state == "PieceSelected":
            k = self.selected
            x1, y1, x2, y2 = self.grid_to_coords(k)

            if self.old_selected == self.selected:
                if self.hover is None:
                    self.unselect()

                    self.selected = None

                elif self.hover == self.selected:
                    self.unselect()

                elif self.hover in self.possible_moves:
                    self.start_move(self.selected, self.hover, snap=True)
                    didMove = True

            else:
                if self.hover is None:
                    self.set(self.selected, "normal", preserve_select=True)

                elif self.hover in self.possible_moves:
                    self.start_move(self.selected, self.hover, snap=True)
                    didMove = True
            if not didMove:
                self.move_obj(self.board[k], (x1 + x2) // 2, (y1 + y2) // 2)

        elif self.state == "Move":
            pass

        if self.hover != None:
            self.set(self.hover, "normal", preserve_select=True)
            self.hover = None

        self.old_selected = self.selected
        self.state = "Nothing"
        self.old_hover = None

    def drag_piece(self, e: tk.Event):
        if self.state == "Nothing" or self.state == "Move":
            return

        x, y = self.coords_to_grid(e.x, e.y)
        x = x if x < 8 else 7
        x = x if x >= 0 else 0
        y = y if y < 8 else 7
        y = y if y >= 0 else 0

        k = x * 10 + y

        self.hover = k

        if self.hover != self.old_hover:
            if self.hover != None and self.old_hover != None:
                self.set(self.old_hover, "normal", preserve_select=True)
            self.old_hover = self.hover
            self.set(self.hover, "button")

        self.move_obj(self.board[self.selected], e.x, e.y)

    def move_obj(self, obj, x, y):
        self.canvas.moveto(obj.img_id, x - obj.i.width() // 2, y - obj.i.height() // 2)

    def unselect(self):
        self.set(self.selected, "normal")
        self.selected = None
        self.old_selected = None
        self.display_moves(False)

    def coords_to_grid(self, x, y):
        x, y = (8 * x // (Chess.size), 8 * y // (Chess.size))
        if self.side == "WHITE":
            return (x, y)
        else:
            return (7 - x, 7 - y)

    def grid_to_coords(self, *args):
        if len(args) == 1:
            x, y = args[0] // 10, args[0] % 10
        elif len(args) == 2:
            x, y = args[0], args[1]

        if self.side == "BLACK":
            x, y = (7 - x, 7 - y)

        return (
            x * Chess.size // 8,
            y * Chess.size // 8,
            (x + 1) * Chess.size // 8,
            (y + 1) * Chess.size // 8,
        )

    def start_move(self, start, end, multi=False, snap=False, times={}):
        t = threading.Thread(
            target=self.move, args=(start, end, multi, snap, times), daemon=True
        )
        t.start()

    def move(self, start, end, multi, snap, times={}):
        self.timers[
            self.me if self.players[self.me]["SIDE"] == self.turn else self.opponent
        ].pause()

        if self.board.fen["HM"]:
            self.timers[
                self.me if self.players[self.me]["SIDE"] == self.turn else self.opponent
            ].add_time(self.add_time)

        if "DRAW" in self.poll:
            if self.poll["DRAW"] == "ACK":
                self.draw_frame.destroy()
                self.send(("DRAW", "ACK", False))
                del self.poll["DRAW"]

            elif self.poll["DRAW"] == "REQ":
                self.send(("DRAW", "DENY"))
                self.draw_ack(False, True)

        self.last_move = [start, end]
        self.board[start].moved(end)
        self.oldimg = self.board[start]
        color = self.board[end].color

        # Enpassant possibility
        if self.board[end].piece == "PAWN":
            if self.last_move[0] - self.last_move[1] == -2:
                self.board.fen["EP"] = Chess.grid_to_square(end - 1)
            elif self.last_move[0] - self.last_move[1] == 2:
                self.board.fen["EP"] = Chess.grid_to_square(end + 1)

        # region How the piece moves
        if snap and not multi:
            x1, y1, x2, y2 = self.grid_to_coords(end)
            self.move_obj(self.board[end], (x1 + x2) // 2, (y1 + y2) // 2)
            self.oldimg = None
        else:
            thr = threading.Thread(
                target=self.moveanimation, args=(start, end), daemon=True
            )
            thr.start()
            self.lock.acquire()

        # endregion

        # region Pawn Promotion
        if self.board[end].piece == "PAWN" and end % 10 in [0, 7]:
            if not multi:
                self.promotion(end)
                self.lock.acquire()

            self.board[end] = ChessPiece(
                self.pawn_promotion, self.board[end].color, self.board, end, self
            )

        # endregion
        self.board.fen.change_turn()
        sent = (start, end, self.pawn_promotion)
        if not multi or self.debug:
            self.send(
                (
                    "MOVE",
                    sent,
                    {
                        self.me: self.timers[self.me].time_left(),
                        self.opponent: self.timers[self.opponent].time_left(),
                    },
                )
            )
            self.display_moves(False)
        else:
            self.timers[self.me].set_time(times[self.me])
            self.timers[self.opponent].set_time(times[self.opponent])
            self.possible_moves = []
        self.pawn_promotion = None

        # region Checking for check
        for i in self.COLOREDSQUARES["move"]:
            self.set(i, state="normal", overide=True)

        a = (start, end)
        for i in a:
            self.set(i, state="select")
        self.COLOREDSQUARES["move"] = a

        if self.COLOREDSQUARES["check"] != None:
            a, self.COLOREDSQUARES["check"] = self.COLOREDSQUARES["check"], None
            self.set(a, "normal")

        self.turn = Chess.swap[self.turn]
        self.timers[
            self.me if self.players[self.me]["SIDE"] == self.turn else self.opponent
        ].resume()

        check = self.board.is_in_check(Chess.swap[color])
        if check:
            i = self.board.locate_king(Chess.swap[color])
            self.set(i, "check")
            self.COLOREDSQUARES["check"] = i

        if self.check_for_mate(Chess.swap[color]):
            self.final_frame(
                "CHECKMATE" if check else "STALEMATE",
                self.me if self.side == color else self.opponent,
            )

    def enable_canvas(self):
        self.canvas.bind("<Button-1>", self.clicked)
        self.canvas.bind("<B1-Motion>", self.drag_piece)
        self.canvas.bind("<ButtonRelease-1>", self.released)
        self.canvas.itemconfig(self.disabled_image, state=tk.HIDDEN)

    def disable_canvas(self, greyed=False):
        self.canvas.unbind("<Button-1>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease-1>")
        if greyed:
            self.canvas.itemconfig(self.disabled_image, state=tk.NORMAL)
            self.canvas.tag_raise(self.disabled_image)

    def promotion(self, end):
        self.disable_canvas(True)
        self.canvas.bind("<Button-1>", self.promotion_click)
        sign = 1 if end % 10 == 0 else -1
        self.pawn_options = {
            end: "QUEEN",
            end + sign * 1: "KNIGHT",
            end + sign * 2: "ROOK",
            end + sign * 3: "BISHOP",
        }
        for i in self.pawn_options.keys():
            self.set(i, "promo")
            self.pawn_options[i] = ChessPiece(
                self.pawn_options[i],
                "BLACK" if sign == -1 else "WHITE",
                self.board,
                i,
                self,
            )

    def promotion_click(self, e):
        x, y = self.coords_to_grid(e.x, e.y)
        k = 10 * x + y

        if k not in self.pawn_options.keys():
            return

        self.pawn_promotion = self.pawn_options[k].piece
        for i in self.pawn_options.keys():
            self.set(i, "normal")
            self.canvas.tag_lower(self.board_ids[i]["base"])
            self.pawn_options[i] = None

        self.enable_canvas()
        self.lock.release()

    def event_handler(self, msg):
        if msg[0] == "LEAVE":
            if msg[1] == "CONN_ERR":
                if not self.isEnded:
                    self.final_frame("CONN", winner=self.me)
            else:
                if not self.isEnded:
                    self.final_frame("RESIGN", winner=self.me)

        elif msg[0] == "MOVE":
            self.opp_move(msg[1], msg[2])
        elif msg[0] == "DRAW":
            if msg[1] == "REQ":
                self.draw_reply()
            elif msg[1] == "ACK":
                self.draw_ack(msg[2])
            elif msg[1] == "DENY":
                self.draw_frame.destroy()
                del self.poll["DRAW"]

    def opp_move(self, msg, times):
        start, end, pawn = msg
        self.chess_notifier(
            "Opponent",
            self.board[start].piece,
            Chess.grid_to_square(end),
            captured=self.board[end],
        )
        if pawn:
            self.pawn_promotion = pawn
        self.start_move(start, end, multi=True, times=times)

    @staticmethod
    def get_active_window():
        if isWin:
            from ctypes import create_unicode_buffer, windll

            hWnd = windll.user32.GetForegroundWindow()
            length = windll.user32.GetWindowTextLengthW(hWnd)
            buf = create_unicode_buffer(length + 1)
            windll.user32.GetWindowTextW(hWnd, buf, length + 1)
            return buf.value if buf.value else None
        else:
            return None

    def chess_notifier(self, opponent, piece, dest, captured=None):
        message = f"{opponent} played {piece.title()} to {dest.upper()}"
        if captured:
            message += f", capturing your {captured.piece.title()}"
        if self.get_active_window() != "Chess" and isWin:
            noti.notify(
                title="Your Turn has started",
                app_name="Arcade",
                message=message,
                timeout=5,
            )

    @staticmethod
    def grid_to_square(k):
        i, j = k % 10, k // 10
        i = str(8 - i)
        j = chr(ord("a") + j)
        return j + i

    @staticmethod
    def square_to_grid(s):
        if s == "-":
            return -1
        i = 8 - int(s[1])
        j = ord(s[0]) - ord("a")
        return j * 10 + i

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
            print("Messagebox Error")

    def draw_req(self):
        self.poll["DRAW"] = "REQ"
        self.send(("DRAW", "REQ"))
        self.draw_frame = tk.Frame(self.main_frame)
        self.draw_frame.place(
            relx=0.5, rely=0.5, anchor="center", relwidth=1, relheight=0.3
        )
        tk.Label(
            self.draw_frame,
            text="Waiting for opponent to respond",
            font=("rockwell", 14),
        ).place(relx=0.5, rely=0.5, anchor="center")

    def final_frame(self, type, winner=None):
        self.isEnded = True
        self.disable_canvas(greyed=True)
        self.protocol("WM_DELETE_WINDOW", lambda: self.quit_game("ENDED"))
        txt = ""
        if type == "DRAW":
            txt = f"The Game is Tied!\n\nPoints:\n\n{self.players[self.me]['NAME']}: ½\n\n{self.players[self.opponent]['NAME']}: ½"
        elif type == "CHECKMATE":
            txt = f"Checkmate!\n\nPoints:\n\n{self.players[self.me]['NAME']}: {1 if self.me==winner else 0}\n\n{self.players[self.opponent]['NAME']}: {1 if self.opponent==winner else 0}"
        elif type == "STALEMATE":
            winner = None
            txt = f"Stalemate!\n\nPoints:\n\n{self.players[self.me]['NAME']}: ½\n\n{self.players[self.opponent]['NAME']}: ½"
        elif type == "CONN":
            txt = f"{self.players[self.opponent]['NAME']} disconnected!\n\nPoints:\n\n{self.players[self.me]['NAME']}: 1\n\n{self.players[self.opponent]['NAME']}: 0"
        elif type == "RESIGN":
            txt = f"{self.players[self.opponent]['NAME']} resigned!\n\nPoints:\n\n{self.players[self.me]['NAME']}: 1\n\n{self.players[self.opponent]['NAME']}: 0"
        elif type == "TIME":
            txt = f"{self.players[self.opponent]['NAME'] if self.me==winner else 'You'} ran out of time!\n\nPoints:\n\n{self.players[self.me]['NAME']}: {1 if self.me==winner else 0}\n\n{self.players[self.opponent]['NAME']}: {1 if self.opponent==winner else 0}"
        else:
            print(f"ERROR: {type} is invalid!")
        self.end_game_frame = tk.Frame(self)
        self.end_game_frame.place(
            relx=0.95, rely=0.5, relheight=0.95, relwidth=0.25, anchor="e"
        )
        tk.Label(
            self.end_game_frame,
            text=txt,
            font=("rockwell", 14),
        ).place(relx=0.5, rely=0.4, anchor="center")

        ttk.Button(
            self.end_game_frame,
            text="EXIT GAME",
            style="20.TButton",
            command=lambda: self.quit_game("ENDED"),
        ).place(relx=0.5, rely=0.8, anchor="center")

        if self.me == winner or (winner is None and self.side == "WHITE"):
            Chess.http.addgame(
                "CHESS",
                self.players[winner]["NAME"] if winner else "none",
                {"board": self.board.fen.value},
                [self.players[self.me]["NAME"], self.players[self.opponent]["NAME"]],
            )  # ? Add PGN

    def draw_ack(self, ack, cancel=False):
        self.draw_frame.destroy()
        if ack:
            self.final_frame("DRAW")
        else:
            if not cancel and isWin:
                noti.notify(
                    title="Declined!",
                    app_name="Chess",
                    message=f"{self.players[self.opponent]['NAME']} has declined your draw offer!",
                    timeout=5,
                )
        del self.poll["DRAW"]

    def draw_reply(self):
        self.poll["DRAW"] = "ACK"
        self.draw_frame = tk.Frame(self.main_frame)
        self.draw_frame.place(
            relx=0.5, rely=0.5, anchor="center", relwidth=1, relheight=0.3
        )
        tk.Label(
            self.draw_frame,
            text="Opponent wants to draw the match!",
            font=("rockwell", 14),
        ).place(relx=0.5, rely=0.25, anchor="center")

        def rep(accept):
            self.draw_frame.destroy()
            if accept:
                self.send(("DRAW", "ACK", True))
                self.final_frame("DRAW")
            else:
                self.send(("DRAW", "ACK", False))
            del self.poll["DRAW"]

        ttk.Button(
            self.draw_frame,
            text="Accept",
            style="13.TButton",
            command=lambda: rep(True),
        ).place(relx=0.25, rely=0.75, anchor="center")

        ttk.Button(
            self.draw_frame,
            text="Decline",
            style="13.TButton",
            command=lambda: rep(False),
        ).place(relx=0.75, rely=0.75, anchor="center")

    def resign(self):
        if self.show_message(
            "Resign the Game?",
            "Are you sure you wish to resign? This will cause your opponent to win by default",
            type="okcancel",
        ):
            self.quit_game("RESIGN")
        else:
            return

    def quit_game(self, reason="None"):
        if __name__ == "__main__":
            Chess.http.logout()
            root.quit()
        else:
            for i in self.timers.values():
                i.stop()
            self.send(("LEAVE", reason))
            self.destroy()
            try:
                self.back_to_arcade()
            except:
                pass


class Piece:
    def __init__(self, piece, color, board, pos):
        self.piece = piece
        self.color = color
        # self.moves: list = []
        self.hasMoved: bool = False
        self.pos = pos
        self.board = board

    def moved(self, pos):
        if not self.hasMoved:
            self.hasMoved = True

            # Castling Posibility Updation
            p = ""
            if self.color == "BLACK":
                p = ("k", "q")
            else:
                p = ("K", "Q")

            if self.piece == "KING":
                self.board.fen["C"] = self.board.fen["C"].replace(p[0], "")
                self.board.fen["C"] = self.board.fen["C"].replace(p[1], "")

            elif self.piece == "ROOK":
                if self.pos // 10 == 0:
                    self.board.fen["C"] = self.board.fen["C"].replace(p[1], "")
                else:
                    self.board.fen["C"] = self.board.fen["C"].replace(p[0], "")

            # Enpassant Availability Checking
            elif self.piece == "PAWN":
                if abs(self.pos - pos) == 2:
                    self.board.fen["EP"] = Chess.grid_to_square((self.pos + pos) // 2)

        # Enpassant movement
        isEnpassant = False
        if self.piece == "PAWN":
            if pos == Chess.square_to_grid(self.board.fen["EP"]):
                print("Enpassant")
                isEnpassant = True
                if pos % 10 == 2:
                    self.board[pos + 1] = None
                elif pos % 10 == 5:
                    self.board[pos - 1] = None
        if not isEnpassant:
            self.board.fen["EP"] = "-"

        # Castling
        if self.piece == "KING":
            if abs(self.pos - pos) == 20:
                print("CASTLE")
                if self.pos > pos:
                    print("Queen Side")
                    self.board[pos - 20].moved(pos + 10)
                else:
                    print("King Side")
                    self.board[pos + 10].moved(pos - 10)

        self.board[pos], self.board[self.pos] = self.board[self.pos], None
        self.pos = pos

    def gen_moves(self, inCheck=False):
        moves = []
        k = self.pos
        board = self.board
        piece = board[k].piece
        color = board[k].color

        if piece == "KING":
            moves.extend([k + 10, k + 11, k + 9, k - 10, k - 9, k - 11, k + 1, k - 1])

            # Check Castling
            temp = "kq" if self.color == "BLACK" else "KQ"
            if temp[0] in board.fen["C"]:
                b = Board(self.board.fen.value)
                for i in range(1, 3):
                    if self.board[k + (i * 10)] != None:
                        break
                    else:
                        b.moved(k + (i - 1) * 10, k + (i * 10))
                        if not inCheck and b.is_in_check(color):
                            break
                else:
                    if not inCheck and not self.board.is_in_check(color):
                        moves.append(k + 20)

            if temp[1] in board.fen["C"]:
                b = Board(self.board.fen.value)
                for i in range(1, 3):
                    if self.board[k - (i * 10)] != None:
                        break
                    else:
                        b.moved(k - (i - 1) * 10, k - (i * 10))
                        if not inCheck and b.is_in_check(color):
                            break
                else:
                    if not inCheck and not self.board.is_in_check(color):
                        moves.append(k - 20)

        elif piece == "KNIGHT":
            moves.extend([k + 8, k - 8, k + 12, k - 12, k + 19, k - 19, k + 21, k - 21])

        elif piece == "PAWN":
            sign = 1 if color == "BLACK" else -1

            # Normal move
            if k + sign in board.keys() and board[k + sign] is None:
                moves.append(k + sign)

            # 2 Step move from start
            if k % 10 == 1 and board[k + 1] is None and board[k + 2] is None:
                if self.color == "BLACK":
                    moves.append(k + 2)

            elif k % 10 == 6 and board[k - 1] is None and board[k - 2] is None:
                if self.color == "WHITE":
                    moves.append(k - 2)

            # Capturing pieces
            if board[k + sign + 10] != None and board[k + sign + 10].color != color:
                moves.append(k + sign + 10)

            if board[k + sign - 10] != None and board[k + sign - 10].color != color:
                moves.append(k + sign - 10)

            # Enpassant
            ep = Chess.square_to_grid(board.fen["EP"])
            if board[k + sign - 10] is None and k + sign - 10 == ep and self.hasMoved:
                moves.append(k + sign - 10)

            if board[k + sign + 10] is None and k + sign + 10 == ep and self.hasMoved:
                moves.append(k + sign + 10)

        elif piece == "QUEEN":
            moves.extend(self.side(board))
            moves.extend(self.diagonal(board))

        elif piece == "ROOK":
            moves.extend(self.side(board))

        elif piece == "BISHOP":
            moves.extend(self.diagonal(board))

        return self.fix(board, moves)

    def side(self, board):
        moves = []
        k = self.pos
        color = board[k].color

        x, y = k // 10, k % 10

        for i in range(x - 1, -1, -1):
            if board[i * 10 + y] != None:
                if board[i * 10 + y].color != color:
                    moves.append(i * 10 + y)
                break
            moves.append(i * 10 + y)

        for i in range(x + 1, 8):
            if board[i * 10 + y] != None:
                if board[i * 10 + y].color != color:
                    moves.append(i * 10 + y)
                break
            moves.append(i * 10 + y)

        for i in range(y - 1, -1, -1):
            if board[10 * x + i] != None:
                if board[10 * x + i].color != color:
                    moves.append(10 * x + i)
                break
            moves.append(10 * x + i)

        for i in range(y + 1, 8):
            if board[10 * x + i] != None:
                if board[10 * x + i].color != color:
                    moves.append(10 * x + i)
                break
            moves.append(10 * x + i)
        return moves

    def diagonal(self, board):
        moves = []
        k = self.pos
        color = board[k].color
        x, y = k // 10, k % 10

        l = x if x < y else y
        for i in range(1, l + 1):
            key = 10 * (x - i) + (y - i)
            if board[key] != None:
                if board[key].color != color:
                    moves.append(key)
                break
            moves.append(key)

        l = (7 - x) if (7 - x) < y else y
        for i in range(1, l + 1):
            key = 10 * (x + i) + (y - i)
            if board[key] != None:
                if board[key].color != color:
                    moves.append(key)
                break
            moves.append(key)

        l = x if x < (7 - y) else (7 - y)
        for i in range(1, l + 1):
            key = 10 * (x - i) + (y + i)
            if board[key] != None:
                if board[key].color != color:
                    moves.append(key)
                break
            moves.append(key)

        l = (7 - x) if (7 - x) < (7 - y) else (7 - y)
        for i in range(1, l + 1):
            key = 10 * (x + i) + (y + i)
            if board[key] != None:
                if board[key].color != color:
                    moves.append(key)
                break
            moves.append(key)

        return moves

    def fix(self, board, moves):
        k = self.pos
        color = board[k].color

        move = []
        for i in moves:
            if i in board.keys() and (board[i] is None or board[i].color != color):
                move.append(i)
                continue

        return move

    def __str__(self):
        return self.piece


class ChessPiece(Piece):
    def __init__(self, piece, color, board, pos, game: Chess):
        super().__init__(piece, color, board, pos)
        self.img_id = None
        self.game: Chess = game
        self.createImage(self.game.canvas, pos)
        self.game.canvas.tag_raise(self.img_id)

    def img(self, color: str, piece: str):
        path = os.path.join(CHESS_ASSETS, "pieces")
        size = int((Chess.size / 8) * 0.75)
        i = (color[0] + "_" + piece + ".png").lower()
        p = os.path.join(path, i)

        return ImageTk.PhotoImage(
            Image.open(p).resize((size, size), Image.Resampling.LANCZOS),
            master=self.game.canvas,
        )

    def createImage(self, canvas: tk.Canvas, key):
        x1, y1, x2, y2 = self.game.grid_to_coords(key)
        self.i = self.img(self.color, self.piece)
        self.img_id = canvas.create_image(
            (x1 + x2) // 2,
            (y1 + y2) // 2,
            anchor=tk.CENTER,
            image=self.i,
        )
        canvas.tag_raise(self.img_id)

    def moved(self, pos):
        old_pos = self.pos
        super().moved(pos)
        if self.piece == "KING":
            if abs(old_pos - pos) == 20:
                move = (0, 0)
                if old_pos < pos:
                    move = (pos + 10, pos - 10)
                else:
                    move = (pos - 20, pos + 10)
                t = threading.Thread(
                    target=self.game.moveanimation,
                    args=(move[0], move[1], True),
                    daemon=True,
                )
                t.start()

    def __str__(self):
        return self.piece


class FEN:

    pieces = {
        "r": "ROOK",
        "n": "KNIGHT",
        "b": "BISHOP",
        "q": "QUEEN",
        "k": "KING",
        "p": "PAWN",
    }
    pieces2 = dict(zip(pieces.values(), pieces.keys()))

    def __init__(self, value):
        self.value = (
            value
            if value
            else "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        )

    def change_turn(self):
        self["T"] = "w" if self["T"] == "b" else "b"
        self["HM"] += 1
        if self["T"] == "w":
            self["FM"] += 1

        self["EP"] = "-"

    def change_board(self, pos, change):
        change = str(change)
        l = self["B"]
        sx, sy = pos % 10, pos // 10

        if change.lower() in FEN.pieces.keys():
            l[sx][sy] = change
        elif change == "-1":
            l[sx][sy] = "-"
        else:
            ex, ey = int(change) % 10, int(change) // 10
            l[ex][ey] = l[sx][sy]
            l[sx][sy] = "-"

        l = FEN.fen_body(l)
        l.extend(self["HEADER"])
        self.assemble_fen(l)

    def split_fen(self):
        return self.value.replace(" ", "/").split("/")

    def assemble_fen(self, l: list):
        l = "/".join(l)
        l: str = l[::-1].replace("/", " ", 5)
        l = l[::-1]
        self.value = l

    def __getitem__(self, key):
        fen = self.split_fen()
        if key[0] == "B":
            if len(key) == 1:
                li = []
                for i in fen[:8]:
                    l = []
                    for j in range(len(i)):
                        if i[j].isdigit():
                            s = "-" * int(i[j])
                            l.extend(list(s))
                        else:
                            l.append(i[j])
                    li.append(l)
                return li
            return fen[int(key[1] - 1)]

        elif key == "T":
            return fen[8]
        elif key == "C":
            return fen[9]
        elif key == "EP":
            return fen[10]
        elif key == "HM":
            return int(fen[11])
        elif key == "FM":
            return int(fen[12])
        elif key == "HEADER":
            return [self["T"], self["C"], self["EP"], str(self["HM"]), str(self["FM"])]

    def __setitem__(self, key, value):
        fen = self.split_fen()
        if key[0] == "B":

            if len(key) == 1:
                a = FEN.digest(value)
                fen[0:8] = a

            else:
                fen[int(key[1] - 1)] = value
        elif key == "T":
            fen[8] = value
        elif key == "C":
            if len(value) == 0:
                fen[9] = "-"
            else:
                fen[9] = value
        elif key == "EP":
            fen[10] = value
        elif key == "HM":
            fen[11] = str(value)
        elif key == "FM":
            fen[12] = str(value)
        self.assemble_fen(fen)

    def __str__(self):
        l = self["B"]
        s = ""
        for i in l:
            for j in i:
                s += j
            s += "\n"
        return s

    @staticmethod
    def fen_body(l):
        l = l[:]
        for i in l:
            j = 0
            while j < len(i):
                if i[j] == "-":
                    c = 0
                    while j < len(i):
                        if i[j] == "-":
                            c += 1
                            i.remove("-")
                        else:
                            i.insert(j, str(c))
                            break
                    else:
                        i.append(str(c))
                else:
                    j += 1
        l = ["".join(i) for i in l]
        return l

    @staticmethod
    def digest(board):
        l = []

        for i in board.values():
            if i is None:
                l.append("-")
            else:
                p = FEN.pieces2[i.piece]
                p = p if i.color == "BLACK" else p.upper()
                l.append(p)

        t = []
        for i in range(8):
            t.append(l[:8])
            l = l[8:]
        return FEN.fen_body(t)


class PGN:
    pieces = FEN.pieces
    pieces2 = FEN.pieces2

    @staticmethod
    def load_move(pgn):
        pass


class Board:
    def __init__(self, fen=None):
        self.fen = FEN(fen)
        self.board: dict[int, Piece] = {}
        self.fen_to_board()

    def fen_to_board(self):
        b = self.fen["B"]
        self.board = {}
        for i in range(len(b)):
            for j in range(len(b[i])):
                if b[i][j] == "-":
                    self.board[j * 10 + i] = None
                else:
                    if b[i][j].islower():
                        self.board[j * 10 + i] = Piece(
                            FEN.pieces[b[i][j]], "BLACK", self, j * 10 + i
                        )
                    else:
                        self.board[j * 10 + i] = Piece(
                            FEN.pieces[b[i][j].lower()], "WHITE", self, j * 10 + i
                        )

    def get_moves(self, k):
        pmoves = self[k].gen_moves()
        moves = []
        for i in pmoves:
            fen = self.fen.value
            # print(fen)
            b = Board(fen)
            b.moved(k, i)
            if not b.is_in_check(b[i].color):
                moves.append(i)
        return moves

    def get_all_moves_of_color(self, color, inCheck=False) -> list:
        m = []
        board = self.board
        for i in board.keys():
            if board[i] != None and board[i].color == color:
                m.extend(board[i].gen_moves(inCheck=inCheck))
        return m

    def moved(self, start, end):
        self[end], self[start] = self[start], None

    def is_in_check(self, color):
        m = self.get_all_moves_of_color(Chess.swap[color], inCheck=True)
        if self.locate_king(color) in m:
            return True
        else:
            return False

    def locate_king(self, color):
        for i in self.keys():
            if self[i] != None and self[i].piece == "KING" and self[i].color == color:
                return i

    def keys(self):
        return self.board.keys()

    def values(self):
        return self.board.values()

    def update(self, value):
        self.board.update(value)
        self.fen["B"] = self.board

    def __getitem__(self, key):
        if key in self.keys():
            return self.board[key]
        else:
            return None

    def __setitem__(self, key, value):
        self.board[key] = value
        self.fen["B"] = self.board

    def __str__(self):
        s = ""
        for i in self.board.keys():
            s += f"{self.board[i]},"
            if i // 10 == 7:
                s += "\n"
        return s


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

    theme = Theme(root, CURR_THEME)

    try:
        os.mkdir(os.path.join(HOME_ASSETS, "cached_pfp"))
    except:
        pass
    hobj = Http("http://167.71.231.52:5000")
    try:
        with open("testcred.txt") as f:
            uname, pwd = eval(f.read())
    except:
        with open("Client/testcred.txt") as f:
            uname, pwd = eval(f.read())
    hobj.login(uname, pwd)
    chess = Chess(
        {
            "ME": "456789",
            "PLAYERS": {
                "123456": {"NAME": uname, "SIDE": "BLACK"},
                "456789": {"NAME": uname, "SIDE": "WHITE"},
            },
            "TIME": 600,
            "ADD_TIME": 5,
        },
        print,
        hobj,
        debug=True,
        theme=theme,
    )
    root.mainloop()
