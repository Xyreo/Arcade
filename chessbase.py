from contextlib import suppress
import tkinter as tk
from PIL import ImageOps, Image, ImageTk
import threading, time, os


class Chess(tk.Tk):
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

    def __init__(self):
        super().__init__()

        self.board: dict[int, Piece] = {}
        self.board_ids: dict = {}
        self.imgs: dict = {}  # TKINTER SUCKS
        self.possible_moves: list = []
        self.initialize_canvas()
        self.initialize_board()
        self.initialize_images()
        self.selected: int = None
        self.hover: int = None
        self.state: str = ""
        self.old_selected = None
        self.old_hover = None
        self.COLOREDSQUARES: dict = {"check": None, "move": []}
        self.special_moves: dict = {"enpassant": (None,), "castle": (None,)}

    def initialize_canvas(self):
        Chess.size = self.winfo_screenheight() * 4 // 5
        self.geometry(
            f"{Chess.size}x{Chess.size}+{self.winfo_screenwidth()//2}+{Chess.size//16}"
        )
        self.canvas = tk.Canvas(
            self,
            highlightthickness=1,
            # highlightbackground='BLACK',
            height=Chess.size,
            width=Chess.size,
        )
        self.canvas.pack()
        for i in range(8):
            for j in range(8):
                s = os.path.join("Chess_Assets", "circle.png")
                self.imgs[i * 10 + j] = (
                    ImageTk.PhotoImage(
                        ImageOps.expand(
                            Image.open(s).resize(
                                (Chess.size // (8 * 4), Chess.size // (8 * 4)),
                                Image.ANTIALIAS,
                            )
                        )
                    ),
                    ImageTk.PhotoImage(
                        ImageOps.expand(
                            Image.open(
                                os.path.join("Chess_Assets", "circle.png")
                            ).resize(
                                (Chess.size // (8), Chess.size // (8)),
                                Image.ANTIALIAS,
                            )
                        )
                    ),
                )

        self.canvas.bind("<Button-1>", self.clicked)
        self.canvas.bind("<B1-Motion>", self.drag_piece)
        self.canvas.bind("<ButtonRelease-1>", self.released)

    def initialize_board(self):

        # region Initializing pieces on Board
        for j in range(8):
            self.board.update({(i * 10 + j): None for i in range(8)})

        self.board.update(
            {
                0: Piece("ROOK", "BLACK", self),
                10: Piece("KNIGHT", "BLACK", self),
                20: Piece("BISHOP", "BLACK", self),
                30: Piece("QUEEN", "BLACK", self),
                40: Piece("KING", "BLACK", self),
                50: Piece("BISHOP", "BLACK", self),
                60: Piece("KNIGHT", "BLACK", self),
                70: Piece("ROOK", "BLACK", self),
                7: Piece("ROOK", "WHITE", self),
                17: Piece("KNIGHT", "WHITE", self),
                27: Piece("BISHOP", "WHITE", self),
                37: Piece("QUEEN", "WHITE", self),
                47: Piece("KING", "WHITE", self),
                57: Piece("BISHOP", "WHITE", self),
                67: Piece("KNIGHT", "WHITE", self),
                77: Piece("ROOK", "WHITE", self),
            }
        )

        for i in range(8):
            self.board[10 * i + 1] = Piece("PAWN", "BLACK", self)
            self.board[10 * i + 6] = Piece("PAWN", "WHITE", self)
        # endregion

        # Board Assets Generation
        offset = 4
        for i in range(8):
            for j in range(8):
                key = i * 10 + j
                x1, y1, x2, y2 = Chess.grid_to_coords(i, j)
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

    def initialize_images(self):

        for key, value in self.board.items():
            if value == None:
                continue
            self.board[key].createImage(self.canvas, key)
            self.canvas.tag_raise(self.board[key].img_id)

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

    def display_moves(self, show: bool = True):

        if show:
            self.possible_moves = self.board[self.selected].generate_moves()

            for i in self.possible_moves:
                if self.board[i] != None:

                    self.canvas.itemconfigure(
                        self.board_ids[i]["hint"], image=self.imgs[i][1]
                    )

                self.canvas.itemconfigure(self.board_ids[i]["hint"], state=tk.NORMAL)
        else:
            for i in self.possible_moves:

                self.canvas.itemconfigure(
                    self.board_ids[i]["hint"], image=self.imgs[i][0]
                )
                self.canvas.itemconfigure(self.board_ids[i]["hint"], state=tk.HIDDEN)
            self.possible_moves = []

    def move(self, k, snap=False):
        update_dict = {k: self.board[self.selected], self.selected: None}
        self.board.update(update_dict)
        self.display_moves(False)

        # region How the piece moves
        if snap:
            x1, y1, x2, y2 = Chess.grid_to_coords(k)
            self.move_obj(self.board[k], (x1 + x2) // 2, (y1 + y2) // 2)
        else:
            thr = threading.Thread(target=self.moveanimation, args=(self.selected, k))
            thr.start()
        # endregion

        # region Checking for special moves
        enpassant = self.special_moves["enpassant"]

        if enpassant[0] == "Maybe":
            if k == enpassant[1]:
                self.special_moves["enpassant"] = ("Yes", k)
            else:
                self.special_moves["enpassant"] = ("No", None)

        elif enpassant[0] == "Yes":
            if k == enpassant[1]:
                sign = -1 if self.board[k].color == "BLACK" else 1
                self.board[k + sign] = None
            else:
                self.special_moves["enpassant"] = ("No", "None")
        # endregion

        # Checking for check
        for i in self.COLOREDSQUARES["move"]:
            self.set(i, state="normal", overide=True)

        a = (self.selected, k)
        for i in a:
            self.set(i, state="select")
        self.COLOREDSQUARES["move"] = a

        m = self.get_all_moves_of_color(self.board, self.board[k].color)
        m = list(dict.fromkeys(m))
        if self.COLOREDSQUARES["check"] != None:
            a, self.COLOREDSQUARES["check"] = self.COLOREDSQUARES["check"], None
            self.set(a, "normal")

        check = False
        for i in m:
            if (
                self.board[i] != None
                and self.board[i].color != self.board[k].color
                and self.board[i].piece == "KING"
            ):
                self.set(i, "check")
                self.COLOREDSQUARES["check"] = i
                check = True

        flag = False
        for i in self.board.keys():
            if self.board[i] != None and self.board[i].color != self.board[k].color:
                if self.idek(self.board[i], self.board, i):
                    flag = True

        if not flag:
            if check:
                print("Checkmate")
            else:
                print("Stalemate")

    def get_all_moves_of_color(self, board, color) -> list:
        m = []
        for i in board.keys():
            if board[i] != None and board[i].color == color:
                m.extend(board[i].generate_moves(context=(i, board)))
        return m

    def idek(self, piece, board, k) -> bool:
        # Returns whether moving the passed piece can prevent check

        m = piece.generate_moves(context=(k, board))
        flag = False
        for i in m:
            b = dict(zip(board.keys(), board.values()))
            b[i], b[k] = b[k], None
            color = "BLACK" if b[i].color != "BLACK" else "WHITE"
            move = self.get_all_moves_of_color(b, color)
            for j in move:
                if b[j] != None and b[j].piece == "KING" and b[j].color == piece.color:
                    break
            else:
                flag = True
                break

        return flag

    def moveanimation(self, s, e):
        x1, y1, x2, y2 = Chess.grid_to_coords(s)
        x, y = (x1 + x2) // 2, (y1 + y2) // 2
        ex1, ey1, ex2, ey2 = Chess.grid_to_coords(e)
        x1, y1 = (ex1 + ex2) // 2 - x, (ey1 + ey2) // 2 - y

        t = 0.05
        fps = 80
        n = int(t * fps)
        for i in range(1, n + 1):
            start = int(x + (i / n) * x1)
            end = int(y + (i / n) * y1)
            time.sleep(t / n)
            self.move_obj(self.board[e], start, end)

    def clicked(self, e):
        x, y = Chess.coords_to_grid(e.x, e.y)
        k = 10 * x + y

        if k in self.possible_moves:
            self.move(k)
            self.state = "Move"

        elif self.board[k] == None:  # or self.board[k].color == 'WHITE':
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
                    self.display_moves(False)

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
            x1, y1, x2, y2 = Chess.grid_to_coords(k)

            if self.old_selected == self.selected:
                if self.hover == None:
                    self.unselect()
                    self.display_moves(False)
                    self.old_selected = None
                    self.selected = None

                elif self.hover == self.selected:
                    self.old_selected = None
                    self.unselect()
                    self.display_moves(False)
                    self.selected = None

                elif self.hover in self.possible_moves:
                    self.move(self.hover, True)
                    didMove = True

                else:
                    pass

            else:
                if self.hover == None:
                    self.set(self.selected, "normal", preserve_select=True)

                elif self.hover in self.possible_moves:
                    self.move(self.hover, True)
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

    def move_obj(self, obj, x, y):
        self.canvas.moveto(obj.img_id, x - obj.i.width() // 2, y - obj.i.height() // 2)

    def unselect(self):
        self.set(self.selected, "normal")

    @staticmethod
    def coords_to_grid(x, y):
        return (8 * x // (Chess.size), 8 * y // (Chess.size))

    @staticmethod
    def grid_to_coords(*args):
        if len(args) == 1:
            x, y = args[0] // 10, args[0] % 10
        elif len(args) == 2:
            x, y = args[0], args[1]

        return (
            x * Chess.size // 8,
            y * Chess.size // 8,
            (x + 1) * Chess.size // 8,
            (y + 1) * Chess.size // 8,
        )


class Piece:
    def __init__(self, piece: str, color: str, game: Chess):
        self.piece = piece
        self.color = color
        self.img_id = None
        self.moves: list = []
        self.game: Chess = game

    @staticmethod
    def img(color: str, piece: str):
        path = os.path.join("Chess_Assets", "128h")
        size = int((Chess.size / 8) * 0.8)
        i = (color[0] + "_" + piece + "_png_128px.png").lower()
        p = os.path.join(path, i)

        return ImageTk.PhotoImage(
            ImageOps.expand(Image.open(p).resize((size, size), Image.ANTIALIAS))
        )

    def createImage(self, canvas: tk.Canvas, key):
        x1, y1, x2, y2 = Chess.grid_to_coords(key)
        self.i = Piece.img(
            self.color, self.piece
        )  # Tkinter Garbage Collection is weird
        self.img_id = canvas.create_image(
            (x1 + x2) // 2,
            (y1 + y2) // 2,
            anchor=tk.CENTER,
            image=self.i,
            # state=tk.HIDDEN,  # TODO
        )

    def generate_moves(self, context: tuple = (None, None)) -> list:
        self.moves = []
        if context[0] == None:
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
            self.moves = [k + 10, k + 11, k + 9, k - 10, k - 9, k - 11, k + 1, k - 1]

        elif piece == "KNIGHT":
            self.moves = [k + 8, k - 8, k + 12, k - 12, k + 19, k - 19, k + 21, k - 21]

        elif piece == "PAWN":
            sign = 1 if color == "BLACK" else -1

            with suppress(KeyError):

                if board[k + sign] == None:
                    self.moves = [k + sign]

                enpassant = self.game.special_moves["enpassant"]
                if context[0] == None and enpassant[0] == "Yes":
                    if k + 10 == enpassant[1]:
                        self.moves.append(k + 10 + sign)
                        self.game.special_moves["enpassant"] = ("Yes", k + 10 + sign)
                    elif k - 10 == enpassant[1]:
                        self.game.special_moves["enpassant"] = ("Yes", k - 10 + sign)
                        self.moves.append(k - 10 + sign)

            if k % 10 == 1 and board[k + 1] == None and board[k + 2] == None:
                if board[k].color == "BLACK":
                    if context[0] == None:
                        self.game.special_moves["enpassant"] = ("Maybe", k + 2)
                    self.moves.append(k + 2)

            elif k % 10 == 6 and board[k - 1] == None and board[k - 2] == None:
                if board[k].color == "WHITE":
                    if context[0] == None:
                        self.game.special_moves["enpassant"] = ("Maybe", k - 2)
                    self.moves.append(k - 2)

            if (
                (k + sign + 10) in board.keys()
                and board[k + sign + 10] != None
                and board[k + sign + 10].color != color
            ):
                self.moves.append(k + sign + 10)

            if (
                (k + sign - 10) in board.keys()
                and board[k + sign - 10] != None
                and board[k + sign - 10].color != color
            ):
                self.moves.append(k + sign - 10)

        elif piece == "QUEEN":
            self.side(context)
            self.diagonal(context)

        elif piece == "ROOK":
            self.side(context)

        elif piece == "BISHOP":
            self.diagonal(context)

        else:
            return Exception

        self.fix(context)
        return self.moves

    def side(self, context: tuple):
        if context[0] == None:
            board: dict = self.game.board
            k = self.game.selected
            color = self.color

        else:
            k = context[0]
            board: dict = context[1]
            color = board[k].color

        x, y = k // 10, k % 10

        for i in range(x - 1, -1, -1):
            if board[i * 10 + y] != None:
                if board[i * 10 + y].color != color:
                    self.moves.append(i * 10 + y)
                break
            self.moves.append(i * 10 + y)

        for i in range(x + 1, 8):
            if board[i * 10 + y] != None:
                if board[i * 10 + y].color != color:
                    self.moves.append(i * 10 + y)
                break
            self.moves.append(i * 10 + y)

        for i in range(y - 1, -1, -1):
            if board[10 * x + i] != None:
                if board[10 * x + i].color != color:
                    self.moves.append(10 * x + i)
                break
            self.moves.append(10 * x + i)

        for i in range(y + 1, 8):
            if board[10 * x + i] != None:
                if board[10 * x + i].color != color:
                    self.moves.append(10 * x + i)
                break
            self.moves.append(10 * x + i)

    def diagonal(self, context: tuple):

        if context[0] == None:
            board: dict = self.game.board
            k = self.game.selected
            color = self.color
        else:
            k = context[0]
            board: dict = context[1]
            color = board[k].color

        x, y = k // 10, k % 10

        l = x if x < y else y
        for i in range(1, l + 1):
            key = 10 * (x - i) + (y - i)
            if board[key] != None:
                if board[key].color != color:
                    self.moves.append(key)
                break
            self.moves.append(key)

        l = (7 - x) if (7 - x) < y else y
        for i in range(1, l + 1):
            key = 10 * (x + i) + (y - i)
            if board[key] != None:
                if board[key].color != color:
                    self.moves.append(key)
                break
            self.moves.append(key)

        l = x if x < (7 - y) else (7 - y)
        for i in range(1, l + 1):
            key = 10 * (x - i) + (y + i)
            if board[key] != None:
                if board[key].color != color:
                    self.moves.append(key)
                break
            self.moves.append(key)

        l = (7 - x) if (7 - x) < (7 - y) else (7 - y)
        for i in range(1, l + 1):
            key = 10 * (x + i) + (y + i)
            if board[key] != None:
                if board[key].color != color:
                    self.moves.append(key)
                break
            self.moves.append(key)

    def fix(self, context: tuple):
        if context[0] == None:
            board: dict = self.game.board
            color = self.color

        else:
            k = context[0]
            board: dict = context[1]
            color = board[k].color

        moves = []
        for i in self.moves:
            if i in board.keys() and (board[i] == None or board[i].color != color):
                if context[0] != None:
                    moves.append(i)
                    continue

                b = dict(zip(board.keys(), board.values()))
                b[i] = b[self.game.selected]
                b[self.game.selected] = None
                m = []
                # At this point, b has assumed the move has been played.
                for j in b.keys():
                    if b[j] != None and b[j].color != self.color:
                        m.extend(self.generate_moves((j, b)))

                m = list(dict.fromkeys(m))
                for j in m:
                    if b[j] != None and b[j].piece == "KING" and b[j].color == color:
                        break
                else:
                    moves.append(i)
        self.moves = moves


if __name__ == "__main__":
    app = Chess()
    app.mainloop()
