import tkinter as tk
import os
from PIL import ImageOps, Image, ImageTk


class Piece:

    @staticmethod
    def img(color, piece):
        path = os.path.join('Chess_Assets', '128h')
        size = int((Chess.size / 8) * 0.8)
        i = (color[0] + '_' + piece + '_png_128px.png').lower()
        p = os.path.join(path, i)

        #print(size)
        return ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open(p).resize((size, size), Image.ANTIALIAS)))

    def __init__(self, piece, color):
        self.piece = piece
        self.color = color
        self.image = Piece.img(color, piece)


class Chess(tk.Tk):
    color = {
        'black': '#eeeed2',
        'white': '#769656',
        'sblack': '#f6f669',
        'swhite': '#baca2b'
    }
    size = 0
    images = {}

    def __init__(self):

        super().__init__()

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
        self.initialize_board()
        self.initialize_images()
        self.isAnySelected = False
        self.isClicked = None

    def initialize_board(self):
        self.pieces = {
            'brook1': Piece('ROOK', 'BLACK'),
            'bknight1': Piece('KNIGHT', 'BLACK'),
            'bbishop1': Piece('BISHOP', 'BLACK'),
            'bqueen': Piece('QUEEN', 'BLACK'),
            'bking': Piece('KING', 'BLACK'),
            'bbishop2': Piece('BISHOP', 'BLACK'),
            'bknight2': Piece('KNIGHT', 'BLACK'),
            'brook2': Piece('ROOK', 'BLACK'),
            'wrook1': Piece('ROOK', 'WHITE'),
            'wknight1': Piece('KNIGHT', 'WHITE'),
            'wbishop1': Piece('BISHOP', 'WHITE'),
            'wqueen': Piece('QUEEN', 'WHITE'),
            'wking': Piece('KING', 'WHITE'),
            'wbishop2': Piece('BISHOP', 'WHITE'),
            'wknight2': Piece('KNIGHT', 'WHITE'),
            'wrook2': Piece('ROOK', 'WHITE'),
        }

        for i in range(8):
            self.pieces['wpawn' + str(i)] = Piece('PAWN', 'WHITE')
            self.pieces['bpawn' + str(i)] = Piece('PAWN', 'BLACK')

        self.gamestate = {
            0: 'brook1',
            10: 'bknight1',
            20: 'bbishop1',
            30: 'bking',
            40: 'bqueen',
            50: 'bbishop2',
            60: 'bknight2',
            70: 'brook2',
            7: 'wrook1',
            17: 'wknight1',
            27: 'wbishop1',
            37: 'wking',
            47: 'wqueen',
            57: 'wbishop2',
            67: 'wknight2',
            77: 'wrook2',
        }

        for i in range(8):
            self.gamestate[10 * i + 1] = f'bpawn{i}'
            self.gamestate[10 * i + 6] = f'wpawn{i}'

        self.gamestate = dict(
            zip(self.gamestate.values(), self.gamestate.keys()))

        self.board_ids = {}

        for i in range(8):
            for j in range(8):
                key = i * 10 + j
                self.board_ids[key] = self.change_board(i, j)
            '''self.canvas.create_text((value[0] + value[1]) // 2,
                                    (value[2] + value[3]) // 2,
                                    anchor=tk.CENTER,
                                    text=str(key))'''

    def initialize_images(self):

        for key, value in self.gamestate.items():
            if value == -1:
                continue
            x1, y1, x2, y2 = Chess.grid_to_coords(value // 10, value % 10)
            Chess.images[self.pieces[key]] = self.canvas.create_image(
                (x1 + x2) // 2, (y1 + y2) // 2,
                anchor=tk.CENTER,
                image=self.pieces[key].image)

    def clicked(self, e):
        x, y = Chess.coords_to_grid(e.x, e.y)
        if (x * 10 + y) not in self.gamestate.values():
            return

        self.isClicked = x * 10 + y
        self.canvas.delete(self.board_ids[x * 10 + y])
        x1, y1, x2, y2 = Chess.grid_to_coords(x, y)
        self.board_ids[x * 10 + y] = self.change_board(x, y, select=True)

    def drag_piece(self, e):
        x, y = Chess.coords_to_grid(e.x, e.y)
        ref = dict(zip(self.gamestate.values(), self.gamestate.keys()))
        #print(ref)
        if not self.isClicked:
            return
        else:
            print(x, y)

    @staticmethod
    def coords_to_grid(x, y):
        return (8 * x // (Chess.size), 8 * y // (Chess.size))

    @staticmethod
    def grid_to_coords(x, y):
        return (x * Chess.size // 8, y * Chess.size // 8,
                (x + 1) * Chess.size // 8, (y + 1) * Chess.size // 8)

    def change_board(self, x, y, select=False, button=False):
        x1, y1, x2, y2 = Chess.grid_to_coords(x, y)
        color = 'white' if (x + y) % 2 else 'black'
        try:
            self.canvas.delete(self.board_ids[x * 10 + y])
        except KeyError:
            pass

        if not button:
            if select:
                c = Chess.color[f's{color}']
            else:
                c = Chess.color[f'{color}']

            rect = self.canvas.create_rectangle(x1,
                                                y1,
                                                x2,
                                                y2,
                                                outline='',
                                                fill=c)
            self.canvas.tag_lower(rect)
            return rect


if __name__ == '__main__':
    app = Chess()
    app.mainloop()