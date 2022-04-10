from contextlib import suppress
import tkinter as tk
from PIL import ImageOps, Image, ImageTk
import threading, time, os

ASSET_PATH = "./Client"


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

    def __init__(self, side, update, debug=False):
        super().__init__()
        self.side = side
        self.board: dict[int, Piece] = Board()
        self.board_ids: dict = {}
        self.imgs: dict = {}  # TKINTER SUCKS
        self.possible_moves: list = []
        self.fen = FEN(None)
        self.initialize_canvas()
        self.initialize_board()
        self.selected: int = None
        self.hover: int = None
        self.state: str = "Nothing"
        self.old_selected = None
        self.old_hover = None
        self.COLOREDSQUARES: dict = {"check": None, "move": []}
        self.special_moves: dict = {"enpassant": None, "castle": []}
        self.last_move: list = [-1, -1]
        self.multiplayer_move = update
        self.turn = "WHITE"
        self.debug = debug

        self.lock = threading.Lock()
        self.lock.acquire(blocking=False)

    def initialize_canvas(self):
        Chess.size = self.winfo_screenheight() * 4 // 5
        self.geometry(
            f"{Chess.size}x{Chess.size}+{self.winfo_screenwidth()//2}+{Chess.size//16}"
        )
        self.title("Chess")
        self.canvas = tk.Canvas(
            self,
            highlightthickness=1,
            height=Chess.size,
            width=Chess.size,
        )
        self.canvas.pack()
        for i in range(8):
            for j in range(8):
                s = os.path.join(ASSET_PATH, "Chess_Assets", "circle.png")
                self.imgs[i * 10 + j] = (
                    ImageTk.PhotoImage(
                        ImageOps.expand(
                            Image.open(s).resize(
                                (Chess.size // (8 * 4), Chess.size // (8 * 4)),
                                Image.Resampling.LANCZOS,
                            )
                        ),
                        master=self.canvas,
                    ),
                    ImageTk.PhotoImage(
                        ImageOps.expand(
                            Image.open(
                                os.path.join(ASSET_PATH, "Chess_Assets", "circle.png")
                            ).resize(
                                (Chess.size // (8), Chess.size // (8)),
                                Image.Resampling.LANCZOS,
                            )
                        ),
                        master=self.canvas,
                    ),
                )

        self.canvas.bind("<Button-1>", self.clicked)
        self.canvas.bind("<B1-Motion>", self.drag_piece)
        self.canvas.bind("<ButtonRelease-1>", self.released)

    def initialize_board(self):

        # region  Board Assets Generation

        offset = 4
        for i in range(8):
            for j in range(8):
                key = i * 10 + j
                x1, y1, x2, y2 = self.grid_to_coords(i, j)
                color = "white" if (i + j) % 2 else "black"
                self.special_moves = {
                    "castle": {"white": ("Y", "Y"), "black": ("Y", "Y")}
                }

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
            font = "Helvetica 14 bold"
            self.canvas.create_text(
                x1 + adj, y1 + adj, text=f"{8-i}", anchor=tk.NW, fill="black", font=font
            )
            self.canvas.create_text(
                x2 - adj,
                y2 - adj,
                text=chr(ord("a") + i),
                anchor=tk.SE,
                fill="black",
                font=font,
            )
        # endregion

        # region Initializing pieces on Board

        board = self.fen["B"]

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

        # endregion

        # region Misc
        self.disimg = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open(
                    os.path.join(ASSET_PATH, "Chess_Assets", "disable.png")
                ).resize((Chess.size, Chess.size), Image.Resampling.LANCZOS)
            ),
            master=self.canvas,
        )
        self.disabled_image = self.canvas.create_image(
            Chess.size // 2,
            Chess.size // 2,
            image=self.disimg,
            anchor=tk.CENTER,
            state=tk.HIDDEN,
        )
        # endregion

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

            enpassant = self.special_moves["enpassant"]
            if enpassant != None:
                self.canvas.itemconfigure(
                    self.board_ids[enpassant[0]]["hint"],
                    image=self.imgs[enpassant[0]][0],
                    state=tk.NORMAL,
                )
            castle = self.special_moves["castle"]
            for i in castle:
                self.canvas.itemconfigure(
                    self.board_ids[i[0]]["hint"],
                    image=self.imgs[i[0]][0],
                    state=tk.NORMAL,
                )

        else:
            for i in self.possible_moves:
                self.canvas.itemconfigure(
                    self.board_ids[i]["hint"], image=self.imgs[i][0], state=tk.HIDDEN
                )

            enpassant = self.special_moves["enpassant"]
            if enpassant != None:
                self.canvas.itemconfigure(
                    self.board_ids[enpassant[0]]["hint"],
                    image=self.imgs[enpassant[0]][0],
                    state=tk.HIDDEN,
                )
            castle = self.special_moves["castle"]
            for i in castle:
                self.canvas.itemconfigure(
                    self.board_ids[i[0]]["hint"],
                    image=self.imgs[i[0]][0],
                    state=tk.HIDDEN,
                )

            self.possible_moves = []
            self.special_moves["enpassant"] = None
            self.special_moves["castle"] = []

    def check_for_check(self, piece, board, k) -> bool:
        # Returns whether moving the passed piece can prevent check

        m = piece.gen_moves(board)
        flag = False
        for i in m:
            b = dict(zip(board.keys(), board.values()))
            b[i], b[k] = b[k], None
            color = Chess.swap[b[i].color]
            move = self.get_all_moves_of_color(b, color)
            for j in move:
                if b[j] != None and b[j].piece == "KING" and b[j].color == piece.color:
                    break
            else:
                flag = True
                break

        return flag

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
            time.sleep(t / n)
            self.move_obj(self.board[e], start, end)
        self.oldimg = None
        if not simul:
            self.lock.release()

    def clicked(self, e):
        x, y = self.coords_to_grid(e.x, e.y)
        k = 10 * x + y

        if k in self.possible_moves or self.inSpecialMove(k):
            self.move(k=k)
            self.state = "Move"

        elif self.board[k] == None or (
            (
                not self.debug
                and (self.board[k].color != self.side or self.side != self.turn)
            )
        ):
            pass

        else:
            self.state = "PieceSelected"

        # Doing stuff

        if self.state == "Nothing":
            if self.selected != None:
                self.unselect()
                self.display_moves(False)

        elif self.state == "PieceSelected":
            if self.selected != k:
                if self.selected != None:
                    self.unselect()

                self.selected = k
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
                if self.hover == None:
                    self.unselect()

                    self.selected = None

                elif self.hover == self.selected:
                    self.unselect()

                elif self.hover in self.possible_moves or self.inSpecialMove(
                    self.hover
                ):
                    self.move(k=self.hover, snap=True)
                    didMove = True

                else:
                    pass

            else:
                if self.hover == None:
                    self.set(self.selected, "normal", preserve_select=True)

                elif self.hover in self.possible_moves or self.inSpecialMove(
                    self.hover
                ):
                    self.move(k=self.hover, snap=True)
                    didMove = True

                else:
                    pass
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

    def inSpecialMove(self, k):
        if self.special_moves["enpassant"] != None:
            if k == self.special_moves["enpassant"][0]:
                return True
        for i in self.special_moves["castle"]:
            if k == i[0]:
                return True

        return False

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

    def move(self, k=None, snap=False, multi=False):
        t = threading.Thread(target=self.fen_move, args=(k, snap, multi))
        t.start()

    def threaded_move(self, k, snap, multi):

        # region updating position

        if multi:
            start, end, special_moves = multi[1]
        else:
            start = self.selected
            end = k
            special_moves = self.special_moves

        self.last_move = [start, end]
        self.board[start].hasMoved = True
        self.board[start].pos = end
        self.oldimg = self.board[start]
        update_dict = {end: self.board[start], start: None}
        self.board.update(update_dict)

        enpassant = special_moves["enpassant"]
        cast = special_moves["castle"]

        if enpassant and end == enpassant[0]:
            self.board[enpassant[1]] = None

        for castle in cast:
            if end == castle[0]:
                self.board[castle[2]], self.board[castle[1]] = (
                    None,
                    self.board[castle[2]],
                )
                thr = threading.Thread(
                    target=self.moveanimation, args=(castle[2], castle[1], True)
                )
                thr.start()
                # self.lock.acquire()

        # endregion

        # region How the piece moves
        if snap:
            x1, y1, x2, y2 = self.grid_to_coords(end)
            self.move_obj(self.board[end], (x1 + x2) // 2, (y1 + y2) // 2)
            self.oldimg = None
        else:
            thr = threading.Thread(target=self.moveanimation, args=(start, end))
            thr.start()
            self.lock.acquire()

        # endregion

        # region Pawn Promotion
        if self.board[end].piece == "PAWN" and end % 10 in [0, 7]:
            if not multi:
                self.promotion(end)
                self.lock.acquire()
                special_moves = self.special_moves

            self.board[end] = Piece(
                special_moves["pawnpromotion"], self.board[end].color, end, self
            )
        elif "pawnpromotion" in self.special_moves.keys():
            del self.special_moves["pawnpromotion"]

        # endregion
        sent = (start, end, self.special_moves)
        if not multi:
            self.multiplayer_move(sent)
            self.display_moves(False)
        else:
            self.possible_moves = []
            self.special_moves["enpassant"] = None
            self.special_moves["castle"] = []
            self.special_moves["pawnpromotion"] = None

        # region Checking for check
        for i in self.COLOREDSQUARES["move"]:
            self.set(i, state="normal", overide=True)

        a = (start, end)
        for i in a:
            self.set(i, state="select")
        self.COLOREDSQUARES["move"] = a

        m = self.get_all_moves_of_color(self.board, self.board[end].color)
        m = list(dict.fromkeys(m))
        if self.COLOREDSQUARES["check"] != None:
            a, self.COLOREDSQUARES["check"] = self.COLOREDSQUARES["check"], None
            self.set(a, "normal")

        check = False
        for i in m:
            if (
                self.board[i] != None
                and self.board[i].color != self.board[end].color
                and self.board[i].piece == "KING"
            ):
                self.set(i, "check")
                self.COLOREDSQUARES["check"] = i
                check = True

        flag = False
        for i in self.board.keys():
            if self.board[i] != None and self.board[i].color != self.board[end].color:
                if self.check_for_check(self.board[i], self.board, i):
                    flag = True

        self.turn = Chess.swap[self.turn]

        if not flag:
            if check:
                print("Checkmate")
            else:
                print("Stalemate")

        # endregion

    def fen_move(self, k, snap, multi):
        # FEN
        self.fen.change_turn()
        if multi:
            start, end, special_moves = multi[1]
        else:
            start = self.selected
            end = k
            special_moves = self.special_moves

        self.last_move = [start, end]
        self.board[start].moved(end)
        self.oldimg = self.board[start]
        update_dict = {end: self.board[start], start: None}
        self.board.update(update_dict)
        # FEN
        self.fen.change_board(start, end)

        enpassant = special_moves["enpassant"]
        cast = special_moves["castle"]

        # Enpassant possibility
        if self.board[end].piece == "PAWN":
            if self.last_move[0] - self.last_move[1] == -2:
                self.fen["EP"] = Chess.grid_to_square(end - 1)
            elif self.last_move[0] - self.last_move[1] == 2:
                self.fen["EP"] = Chess.grid_to_square(end + 1)

        # endregion

        if enpassant and end == enpassant[0]:
            self.board[enpassant[1]] = None

        for castle in cast:
            if end == castle[0]:
                self.board[castle[2]], self.board[castle[1]] = (
                    None,
                    self.board[castle[2]],
                )
                # FEN
                self.fen.change_board(castle[2], castle[1])

                thr = threading.Thread(
                    target=self.moveanimation, args=(castle[2], castle[1], True)
                )
                thr.start()

        # endregion

        # region How the piece moves
        if snap:
            x1, y1, x2, y2 = self.grid_to_coords(end)
            self.move_obj(self.board[end], (x1 + x2) // 2, (y1 + y2) // 2)
            self.oldimg = None
        else:
            thr = threading.Thread(target=self.moveanimation, args=(start, end))
            thr.start()
            self.lock.acquire()

        # endregion

        # region Pawn Promotion
        if self.board[end].piece == "PAWN" and end % 10 in [0, 7]:
            if not multi:
                self.promotion(end)
                self.lock.acquire()
                special_moves = self.special_moves

            self.board[end] = Piece(
                special_moves["pawnpromotion"], self.board[end].color, end, self
            )
            # PGN
            p = FEN.pieces2[special_moves["pawnpromotion"]]
            p = p if self.board[end].color == "BLACK" else p.upper()
            print(p)
            self.fen.change_board(end, p)

        elif "pawnpromotion" in self.special_moves.keys():
            del self.special_moves["pawnpromotion"]

        # endregion
        sent = (start, end, self.special_moves)
        if not multi:
            self.multiplayer_move(sent)
            self.display_moves(False)
        else:
            self.possible_moves = []
            self.special_moves["enpassant"] = None
            self.special_moves["castle"] = []
            self.special_moves["pawnpromotion"] = None

        # region Checking for check
        for i in self.COLOREDSQUARES["move"]:
            self.set(i, state="normal", overide=True)

        a = (start, end)
        for i in a:
            self.set(i, state="select")
        self.COLOREDSQUARES["move"] = a

        m = self.get_all_moves_of_color(self.board, self.board[end].color)
        m = list(dict.fromkeys(m))
        if self.COLOREDSQUARES["check"] != None:
            a, self.COLOREDSQUARES["check"] = self.COLOREDSQUARES["check"], None
            self.set(a, "normal")

        check = False
        for i in m:
            if (
                self.board[i] != None
                and self.board[i].color != self.board[end].color
                and self.board[i].piece == "KING"
            ):
                self.set(i, "check")
                self.COLOREDSQUARES["check"] = i
                check = True

        flag = False
        for i in self.board.keys():
            if self.board[i] != None and self.board[i].color != self.board[end].color:
                if self.check_for_check(self.board[i], self.board, i):
                    flag = True

        self.turn = Chess.swap[self.turn]

        if not flag:
            if check:
                print("Checkmate")
            else:
                print("Stalemate")

        # endregion
        print(self.fen.value)

    def pgn_move(self, pgn):
        self.fen.change_turn()  # DUPLICATE
        color = "BLACK" if self.fen["T"] == "b" else "WHITE"

    def enable_canvas(self):
        self.canvas.bind("<Button-1>", self.clicked)
        self.canvas.bind("<B1-Motion>", self.drag_piece)
        self.canvas.bind("<ButtonRelease-1>", self.released)
        self.canvas.itemconfig(self.disabled_image, state=tk.HIDDEN)

    def disable_canvas(self):
        self.canvas.unbind("<Button-1>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease-1>")
        self.canvas.itemconfig(self.disabled_image, state=tk.NORMAL)
        self.canvas.tag_raise(self.disabled_image)

    def promotion(self, end):
        # self.disable_canvas()
        self.canvas.bind("<Button-1>", self.promotion_click)
        sign = 1 if end % 10 == 0 else -1
        self.pawn_options = {
            end: "QUEEN",
            end + sign * 1: "KNIGHT",
            end + sign * 2: "ROOk",
            end + sign * 3: "BISHOP",
        }
        for i in self.pawn_options.keys():
            self.set(i, "promo")
            self.pawn_options[i] = Piece(
                self.pawn_options[i], "BLACK" if sign == -1 else "WHITE", i, self
            )

    def promotion_click(self, e):
        x, y = self.coords_to_grid(e.x, e.y)
        k = 10 * x + y

        if k not in self.pawn_options.keys():
            return

        self.special_moves["pawnpromotion"] = self.pawn_options[k].piece
        for i in self.pawn_options.keys():
            self.set(i, "normal")
            self.canvas.tag_lower(self.board_ids[i]["base"])
            self.pawn_options[i] = None

        self.enable_canvas()
        self.lock.release()

    @staticmethod
    def grid_to_square(k):
        i, j = k % 10, k // 10
        i = str(8 - i)
        j = chr(ord("a") + j)
        return j + i

    @staticmethod
    def square_to_grid(s):
        i = 8 - int(s[1])
        j = ord(s[0]) - ord("a")
        return j * 10 + i


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
            p = ""
            if self.color == "BLACK":
                p = ("k", "q")
            else:
                p = ("K", "Q")

            if self.piece == "KING":
                self.board.fen["C"] = self.board.fen["C"].replace(p[0], "")
                self.board.fen["C"] = self.game.fen["C"].replace(p[1], "")

            elif self.piece == "ROOK":
                if self.pos // 10 == 0:
                    self.board.fen["C"] = self.board.fen["C"].replace(p[1], "")
                else:
                    self.board.fen["C"] = self.board.fen["C"].replace(p[0], "")

            elif self.piece == "PAWN":
                if abs(self.pos - pos) == "2":
                    self.board.fen["EP"] = (self.pos + pos) // 2

        self.pos = pos

    def generate_moves(self, context: tuple = (None, None)) -> list:
        moves = []
        if context[0] == None:
            self.moves = moves
            board: dict[int, Piece] = self.game.board
            k = self.game.selected
            piece = board[k].piece
            color = self.color

        else:
            k = context[0]
            board: dict[int, Piece] = context[1]
            piece = board[k].piece
            color = board[k].color

        if piece == "KING":
            moves.extend([k + 10, k + 11, k + 9, k - 10, k - 9, k - 11, k + 1, k - 1])
            if not self.hasMoved and context[0] == None:
                n = self.pos - 40
                if board[n] != None and not (board[n].hasMoved):
                    temp = [n + 10, n + 20, n + 30]
                    for i in temp:
                        if not board[i]:
                            b = dict(zip(board.keys(), board.values()))
                            b[i], b[self.pos] = b[self.pos], None
                            c = Chess.swap[self.color]
                            m = self.game.get_all_moves_of_color(b, c)
                            if i in m:
                                break
                        else:
                            break
                    else:
                        self.game.special_moves["castle"] = [
                            (n + 20, n + 30, n),
                        ]
                n = self.pos + 30
                if board[n] != None and not (board[n].hasMoved):
                    temp = [n - 10, n - 20]
                    for i in temp:
                        if not board[i]:
                            b = dict(zip(board.keys(), board.values()))
                            b[i], b[self.pos] = b[self.pos], None
                            c = Chess.swap[self.color]
                            m = self.game.get_all_moves_of_color(b, c)
                            if i in m:
                                break
                        else:
                            break
                    else:
                        self.game.special_moves["castle"].append((n - 10, n - 20, n))

        elif piece == "KNIGHT":
            moves.extend([k + 8, k - 8, k + 12, k - 12, k + 19, k - 19, k + 21, k - 21])

        elif piece == "PAWN":
            sign = 1 if color == "BLACK" else -1

            with suppress(KeyError):
                if board[k + sign] == None:
                    moves.append(k + sign)
                l = self.game.last_move
                if (
                    k + 10 == l[1]
                    and board[k + 10] != None
                    and board[k + 10].piece == "PAWN"
                    and board[k + 10].color != color
                    and abs(l[0] - l[1]) == 2
                ):
                    self.game.special_moves["enpassant"] = (k + 10 + sign, k + 10)

                if (
                    k - 10 == l[1]
                    and board[k - 10] != None
                    and board[k - 10].piece == "PAWN"
                    and board[k - 10].color != color
                    and abs(l[0] - l[1]) == 2
                ):
                    self.game.special_moves["enpassant"] = (k - 10 + sign, k - 10)

            if k % 10 == 1 and board[k + 1] == None and board[k + 2] == None:
                if board[k].color == "BLACK":
                    moves.append(k + 2)

            elif k % 10 == 6 and board[k - 1] == None and board[k - 2] == None:
                if board[k].color == "WHITE":
                    moves.append(k - 2)

            if (
                (k + sign + 10) in board.keys()
                and board[k + sign + 10] != None
                and board[k + sign + 10].color != color
            ):
                moves.append(k + sign + 10)

            if (
                (k + sign - 10) in board.keys()
                and board[k + sign - 10] != None
                and board[k + sign - 10].color != color
            ):
                moves.append(k + sign - 10)

        elif piece == "QUEEN":
            moves.extend(self.side(context))
            moves.extend(self.diagonal(context))

        elif piece == "ROOK":
            moves.extend(self.side(context))

        elif piece == "BISHOP":
            moves.extend(self.diagonal(context))

        else:
            return Exception

        tmove = self.fix(context, moves)
        moves.clear()
        moves.extend(tmove)
        return moves

    def gen_moves(self):
        moves = []
        k = self.pos
        board = self.board
        piece = board[k].piece
        color = board[k].color
        if piece == "KING":
            moves.extend([k + 10, k + 11, k + 9, k - 10, k - 9, k - 11, k + 1, k - 1])
            temp = "kq" if self.color == "BLACK" else "KQ"
            if temp[0] in board.fen["T"]:
                pass
            if temp[1] in board.fen["T"]:
                pass
        elif piece == "KNIGHT":
            moves.extend([k + 8, k - 8, k + 12, k - 12, k + 19, k - 19, k + 21, k - 21])

        elif piece == "PAWN":
            sign = 1 if color == "BLACK" else -1
            moves.append(k + sign)

            if k % 10 == 1 and board[k + 1] == None and board[k + 2] == None:
                if board[k].color == "BLACK":
                    moves.append(k + 2)

            elif k % 10 == 6 and board[k - 1] == None and board[k - 2] == None:
                if board[k].color == "WHITE":
                    moves.append(k - 2)

            if board[k + sign + 10] != None and board[k + sign + 10].color != color:
                moves.append(k + sign + 10)

            if board[k + sign - 10] != None and board[k + sign - 10].color != color:
                moves.append(k + sign - 10)

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
            if i in board.keys() and (board[i] == None or board[i].color != color):
                move.append(i)
                continue

        return move

    def get(self):
        return (self.piece, self.color, self.pos)


class ChessPiece(Piece):
    def __init__(self, piece, color, board, pos, game: Chess):
        super().__init__(piece, color, board, pos)
        self.img_id = None
        self.game: Chess = game
        self.createImage(self.game.canvas, pos)
        self.game.canvas.tag_raise(self.img_id)

    def img(self, color: str, piece: str):
        path = os.path.join(ASSET_PATH, "Chess_Assets", "128h")
        size = int((Chess.size / 8) * 0.75)
        i = (color[0] + "_" + piece + "_png_128px.png").lower()
        p = os.path.join(path, i)

        return ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open(p).resize((size, size), Image.Resampling.LANCZOS)
            ),
            master=self.game.canvas,
        )

    def createImage(self, canvas: tk.Canvas, key):
        x1, y1, x2, y2 = self.game.grid_to_coords(key)
        self.i = self.img(self.color, self.piece)  # Tkinter Garbage Collection is weird
        self.img_id = canvas.create_image(
            (x1 + x2) // 2,
            (y1 + y2) // 2,
            anchor=tk.CENTER,
            image=self.i,
            # state=tk.HIDDEN,  # TODO
        )
        canvas.tag_raise(self.img_id)


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
                            l.extend([p for p in s])
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
                fen[0:8] = FEN.digest(value)
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
            if i == None:
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


class Move:
    def __init__(self, start, end, board):
        self.piece = board[start].get()
        self.start = start
        self.end = end
        if board[end] != None:
            self.capture = board[end].get()
        else:
            self.capture = None
        self.state = board
        self.enpassant = None

    def validate(self):
        pass


class Castle(Move):
    def __init__(self, side, board):
        pos = ()
        self.rook = ()
        if side == "q":
            pos = (40, 20)
            self.rook(0, 30)
        elif side == "Q":
            pos = (47, 27)
            self.rook(7, 37)
        elif side == "k":
            pos = (40, 60)
            self.rook(70, 50)
        elif side == "K":
            pos = (47, 67)
            self.rook(77, 57)
        super.__init__(pos[0], pos[1], board)

    def validate(self):
        pass


class Enpassant(Move):
    def __init__(self, start, target, board):
        end = target + 1 if start % 10 == 6 else target - 1
        super.__init__(start, end, board)
        self.capture = target

    def valiate(self):
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
                            FEN.pieces[b[i][j]], "BLACK", self.board, j * 10 + i
                        )
                    else:
                        self.board[j * 10 + i] = Piece(
                            FEN.pieces[b[i][j].lower()], "WHITE", self.board, j * 10 + i
                        )

    def get_moves(self, k):
        pmoves = self[k].gen_moves()
        moves = []
        for i in pmoves:
            fen = self.fen.value
            b = Board(fen)
            b.moved(k, i)
            if not b.is_in_check(b[i].color):
                moves.append(i)
        return moves

    def get_all_moves_of_color(self, color) -> list:
        m = []
        board = self.board
        for i in board.keys():
            if board[i] != None and board[i].color == color:
                m.extend(board[i].gen_moves())
        return m

    def moved(self, start, end):
        fen = self.fen
        print(self.board)
        if self.board[start].piece == "PAWN" and end == fen["EP"]:
            pass
        elif self.board[start].piece == "KING" and abs(start - end) == 2:
            pass

        self.board[end], self.board[start] = self.board[start], None

    def is_in_check(self, color):
        m = self.get_all_moves_of_color(Chess.swap[color])
        for i in self.board.keys():
            if (
                self.board[i] != None
                and self.board[i].color == color
                and self.board[i].piece == "KING"
            ):
                if i in m:
                    return True
                else:
                    return False

    # region data stuff
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
        return str(self.fen)

    # endregion


if __name__ == "__main__":
    app = tk.Tk()
    app.withdraw()
    chess = Chess("WHITE", print, debug=True)
    app.mainloop()
