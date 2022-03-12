from contextlib import suppress
import tkinter as tk
import os
import copy
from PIL import ImageOps, Image, ImageTk


class Chess(tk.Tk):
    color = {
        'black': '#eeeed2',
        'white': '#769656',
        'sblack': '#f6f669',
        'swhite': '#baca2b',
        'sbwhite': '#fcfccb',
        'sbblack': '#e7edb5',
        'bwhite': '#cfdac4',
        'bblack': '#f9f9ef',
        'hint': '#d6d6bd'
    }
    size = None

    def __init__(self):
        super().__init__()

        self.board: dict = {}
        self.board_ids: dict = {}
        self.possible_moves: list = []
        self.gamestate = Gamestate(self)
        self.initialize_canvas()
        self.initialize_board()
        self.initialize_images()

    def initialize_canvas(self):
        Chess.size = self.winfo_screenheight() * 4 // 5
        self.geometry(
            f'{Chess.size}x{Chess.size}+{self.winfo_screenwidth()//2}+{Chess.size//16}'
        )
        self.canvas = tk.Canvas(
            self,
            highlightthickness=1,
            #highlightbackground='BLACK',
            height=Chess.size,
            width=Chess.size)
        self.canvas.pack()

        self.canvas.bind('<Button-1>', self.clicked)
        self.canvas.bind('<B1-Motion>', self.drag_piece)
        self.canvas.bind('<ButtonRelease-1>', self.released)

    def initialize_board(self):

        #region Initializing pieces on Board
        self.selected_sqaures = {}
        for j in range(8):
            self.board.update({(i * 10 + j): None for i in range(8)})
            self.selected_sqaures.update({(i * 10 + j): None
                                          for i in range(8)})

        self.board.update({
            0: Piece('ROOK', 'BLACK'),
            10: Piece('KNIGHT', 'BLACK'),
            20: Piece('BISHOP', 'BLACK'),
            30: Piece('QUEEN', 'BLACK'),
            40: Piece('KING', 'BLACK'),
            50: Piece('BISHOP', 'BLACK'),
            60: Piece('KNIGHT', 'BLACK'),
            70: Piece('ROOK', 'BLACK'),
            7: Piece('ROOK', 'WHITE'),
            17: Piece('KNIGHT', 'WHITE'),
            27: Piece('BISHOP', 'WHITE'),
            37: Piece('QUEEN', 'WHITE'),
            47: Piece('KING', 'WHITE'),
            57: Piece('BISHOP', 'WHITE'),
            67: Piece('KNIGHT', 'WHITE'),
            77: Piece('ROOK', 'WHITE'),
        })

        for i in range(8):
            self.board[10 * i + 1] = Piece('PAWN', 'BLACK')
            self.board[10 * i + 6] = Piece('PAWN', 'WHITE')
        #endregion

        #Board Assets Generation
        offset = 4
        off1 = 30
        for i in range(8):
            for j in range(8):
                key = i * 10 + j
                x1, y1, x2, y2 = Chess.grid_to_coords(i, j)
                color = 'white' if (i + j) % 2 else 'black'

                base = self.canvas.create_rectangle(x1,
                                                    y1,
                                                    x2,
                                                    y2,
                                                    fill=Chess.color[color],
                                                    outline='',
                                                    state='normal')

                highlight_square = self.canvas.create_rectangle(
                    x1 + offset,
                    y1 + offset,
                    x2 - offset,
                    y2 - offset,
                    fill=Chess.color['b' + color],
                    outline='',
                    state='hidden')

                hint = self.canvas.create_oval(x1 + off1,
                                               y1 + off1,
                                               x2 - off1,
                                               y2 - off1,
                                               fill=Chess.color['hint'],
                                               outline='',
                                               state='hidden')

                self.board_ids[key] = {
                    'base': base,
                    'button': highlight_square,
                    'hint': hint,
                }

    def initialize_images(self):

        for key, value in self.board.items():
            if value == None:
                continue
            self.board[key].createImage(self.canvas, key)
            self.canvas.tag_raise(self.board[key].img_id)

    def set(self, id: int, state: str, preserve_select=False):

        color = 'white' if (id // 10 + id % 10) % 2 else 'black'
        if state == 'normal':
            if preserve_select and id == self.gamestate.selected:
                self.set(id, state='select')
                return

            color = Chess.color[color]
            self.canvas.itemconfigure(self.board_ids[id]['button'],
                                      state='hidden')
            self.canvas.itemconfigure(self.board_ids[id]['base'], fill=color)

        elif state == 'select':
            color = Chess.color['s' + color]
            self.canvas.itemconfigure(self.board_ids[id]['base'], fill=color)

        elif state == 'button':
            c1 = 'b' + color
            c2 = color
            if id == self.gamestate.selected:
                c1 = 's' + c1
                c2 = 's' + c2

            self.canvas.itemconfigure(self.board_ids[id]['button'],
                                      state='normal',
                                      fill=Chess.color[c2])
            self.canvas.itemconfigure(self.board_ids[id]['base'],
                                      fill=Chess.color[c1])

    def clicked(self, e):
        self.gamestate.describe()
        x, y = Chess.coords_to_grid(e.x, e.y)
        k = 10 * x + y
        self.gamestate.update_click(k)
        self.gamestate.describe()
        print('-' * 40)

        if self.gamestate.state == 'Nothing':
            if self.gamestate.selected != None:
                self.unselect()

        elif self.gamestate.state == 'Move':
            pass

        elif self.gamestate.state == 'PieceSelected':
            if self.gamestate.selected != k:
                if self.gamestate.selected != None:
                    self.unselect()
                self.gamestate.selected = k
                self.set(k, 'select')
                self.set(k, 'button')

            self.canvas.tag_raise(self.board[k].img_id)
            self.move_obj(self.board[k], e.x, e.y)

    def released(self, e: tk.Event):

        if self.gamestate.state == 'Nothing':
            return

        elif self.gamestate.state == 'PieceSelected':
            k = self.gamestate.selected
            x1, y1, x2, y2 = Chess.grid_to_coords(k)
            game: Gamestate = self.gamestate

            if game.old_selected == game.selected:
                if game.hover == None:
                    self.unselect()
                    self.gamestate.old_selected = None
                    self.gamestate.selected = None

                elif game.hover == game.selected:
                    self.gamestate.old_selected = None
                    self.unselect()
                    self.gamestate.selected = None

                elif game.hover in self.possible_moves:
                    pass

                else:
                    pass

            else:
                if game.hover == None:
                    self.set(self.gamestate.selected,
                             'normal',
                             preserve_select=True)

                elif game.hover in self.possible_moves:
                    pass

                else:
                    pass

            self.move_obj(self.board[k], (x1 + x2) // 2, (y1 + y2) // 2)

        elif self.gamestate.state == 'Move':
            pass
        if self.gamestate.hover != None:
            self.set(self.gamestate.hover, 'normal', preserve_select=True)
            self.gamestate.hover = None

        self.gamestate.old_selected = self.gamestate.selected
        self.gamestate.state = 'Nothing'
        self.gamestate.old_hover = None

    def drag_piece(self, e: tk.Event):

        if self.gamestate.state == 'Nothing':
            return

        x, y = self.coords_to_grid(e.x, e.y)
        k = x * 10 + y
        self.gamestate.hover = k

        if self.gamestate.hover != self.gamestate.old_hover:
            if self.gamestate.hover != None and self.gamestate.old_hover != None:
                #TODO Switchero
                self.set(self.gamestate.old_hover,
                         'normal',
                         preserve_select=True)
            self.gamestate.old_hover = self.gamestate.hover
            self.set(self.gamestate.hover, 'button')

        self.move_obj(self.board[self.gamestate.selected], e.x, e.y)

    def move_obj(self, obj, x, y):
        self.canvas.moveto(obj.img_id, x - obj.i.width() // 2,
                           y - obj.i.height() // 2)

    def unselect(self):
        self.set(self.gamestate.selected, 'normal')

    @staticmethod
    def coords_to_grid(x, y):
        return (8 * x // (Chess.size), 8 * y // (Chess.size))

    @staticmethod
    def grid_to_coords(*args):
        if len(args) == 1:
            x, y = args[0] // 10, args[0] % 10
        elif len(args) == 2:
            x, y = args[0], args[1]

        return (x * Chess.size // 8, y * Chess.size // 8,
                (x + 1) * Chess.size // 8, (y + 1) * Chess.size // 8)


class Gamestate:

    def __init__(self, game: Chess) -> None:
        self.game: Chess = game
        self.selected: int = None
        self.hover: int = None
        self.state: str = ''
        self.old_selected = None
        self.old_hover = None

    def update_click(self, key: int) -> None:

        if self.game.board[key] == None:
            pass

        elif key in self.game.possible_moves:
            self.state = 'Move'

        else:
            self.state = 'PieceSelected'

    def update_release(self, key: int):
        self.state = ''

    def describe(self):  #Sanity has abandoed me
        '''print('State: ', self.state)
        print('Selected: ', self.selected)
        print('Hover: ', self.hover)
        print('Old Selected: ', self.old_selected)
        print('Old Hover: ', self.old_hover)
        print()'''
        pass


class Piece:

    @staticmethod
    def img(color: str, piece: str):
        path = os.path.join('Chess_Assets', '128h')
        size = int((Chess.size / 8) * 0.8)
        i = (color[0] + '_' + piece + '_png_128px.png').lower()
        p = os.path.join(path, i)

        #print(size)
        return ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open(p).resize((size, size), Image.ANTIALIAS)))

    def __init__(self, piece: str, color: str):
        self.piece = piece
        self.color = color
        self.img_id = None

    def createImage(self, canvas: tk.Canvas, key):
        x1, y1, x2, y2 = Chess.grid_to_coords(key)
        self.i = Piece.img(self.color,
                           self.piece)  #Tkinter Garbage Collection is weird
        self.img_id = canvas.create_image((x1 + x2) // 2, (y1 + y2) // 2,
                                          anchor=tk.CENTER,
                                          image=self.i)

    def move(self, game: Chess) -> list:
        self.potential_moves = []
        k = game.isClicked
        print(k)

        if self.piece == 'KING':
            self.potential_moves = [
                k + 10, k + 11, k + 9, k - 10, k - 9, k - 11, k + 1, k - 1
            ]
            self.fix()

        elif self.piece == 'KNIGHT':
            self.potential_moves = [
                k + 8, k - 8, k + 12, k - 12, k + 19, k - 19, k + 21, k - 21
            ]
            self.fix()

        elif self.piece == 'PAWN':
            sign = 1 if self.color == 'BLACK' else -1
            self.potential_moves = [k + sign]
            if k % 10 == 1:
                self.potential_moves.append(k + 2)
            elif k % 10 == 6:
                self.potential_moves.append(k - 2)

            with suppress(KeyError):
                if game.board[k + sign + 10] != None and game.board[
                        k + sign - 10].color != self.color:
                    self.potential_moves.append(k + sign + 10)

                if game.board[k + sign - 10] != None and game.board[
                        k + sign - 10].color != self.color:
                    self.potential_moves.append(k + sign - 10)

            self.fix()

        elif self.piece == 'QUEEN':
            self.side(game)
            self.diagonal(game)

        elif self.piece == 'ROOK':
            self.side(game)

        elif self.piece == 'BISHOP':
            self.diagonal(game)

        else:
            return Exception

        return self.potential_moves

    def side(self, game):
        k = game.isClicked
        x, y = k // 10, k % 10
        for i in range(x - 1, -1, -1):
            if game.board[i * 10 + y] != None:
                if game.board[i * 10 + y].color != self.color:
                    self.potential_moves.append(i * 10 + y)
                break
            self.potential_moves.append(i * 10 + y)

        for i in range(x + 1, 8):
            if game.board[i * 10 + y] != None:
                if game.board[i * 10 + y].color != self.color:
                    self.potential_moves.append(i * 10 + y)
                break
            self.potential_moves.append(i * 10 + y)

        for i in range(y - 1, -1, -1):
            if game.board[x + i] != None:
                if game.board[x + i].color != self.color:
                    self.potential_moves.append(x + i)
                break
            self.potential_moves.append(x + i)

        for i in range(y + 1, 8):
            print(x, y, i)
            if game.board[x + i] != None:
                if game.board[x + i].color != self.color:
                    self.potential_moves.append(x + i)
                break
            self.potential_moves.append(x + i)

    def diagonal(self, game):
        k = game.isClicked
        x, y = k // 10, k % 10
        l = x if x < y else y
        for i in range(1, l):
            key = 10 * (x - i) + (y - i)
            if game.board[key] != None:
                if game.board[key].color != self.color:
                    self.potential_moves.append(key)
                break
            self.potential_moves.append(key)

        l = (8 - x) if (8 - x) < y else y
        for i in range(1, l):
            key = 10 * (x + i) + (y - i)
            if game.board[key] != None:
                if game.board[key].color != self.color:
                    self.potential_moves.append(key)
                break
            self.potential_moves.append(key)

        l = x if x < (8 - y) else (8 - y)
        for i in range(1, l):
            key = 10 * (x - i) + (y + i)
            if game.board[key] != None:
                if game.board[key].color != self.color:
                    self.potential_moves.append(key)
                break
            self.potential_moves.append(key)

        l = (8 - x) if (8 - x) < (8 - y) else (8 - y)
        for i in range(1, l):
            key = 10 * (x + i) + (y + i)
            if game.board[key] != None:
                if game.board[key].color != self.color:
                    self.potential_moves.append(key)
                break
            self.potential_moves.append(key)

    def fix(self):
        m = []
        for i in self.potential_moves:
            if (0 <= i // 10 < 8) and (0 <= i % 10 < 8):
                m.append(i)
        self.potential_moves = m
        #PAIN AND SUFFERING HELP ME


if __name__ == '__main__':
    app = Chess()
    app.mainloop()