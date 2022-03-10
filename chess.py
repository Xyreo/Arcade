import tkinter as tk
import os
import copy
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
        self.img_id = None

    def createImage(self, canvas, key):
        x1, y1, x2, y2 = Chess.grid_to_coords(key)
        self.i = Piece.img(self.color,
                           self.piece)  #Tkinter Garbage Collection is weird
        self.img_id = canvas.create_image((x1 + x2) // 2, (y1 + y2) // 2,
                                          anchor=tk.CENTER,
                                          image=self.i)


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
    }
    size = None

    def __init__(self):
        super().__init__()

        self.board = {}
        self.board_ids = {}
        self.initialize_canvas()
        self.initialize_board()
        self.initialize_images()
        self.isClicked = None
        self.isHover = None
        self.secondClick = None  #Purely for cosmetics

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

                self.board_ids[key] = {
                    'base': base,
                    'button': highlight_square,
                }

    def initialize_images(self):

        for key, value in self.board.items():
            if value == None:
                continue
            self.board[key].createImage(self.canvas, key)
            self.canvas.tag_raise(self.board[key].img_id)

    def set(self, id, state, preserve_select=False):

        color = 'white' if (id // 10 + id % 10) % 2 else 'black'
        if state == 'normal':
            if preserve_select and id == self.isClicked:
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
            if id == self.isClicked:
                c1 = 's' + c1
                c2 = 's' + c2

            self.canvas.itemconfigure(self.board_ids[id]['button'],
                                      state='normal',
                                      fill=Chess.color[c2])
            self.canvas.itemconfigure(self.board_ids[id]['base'],
                                      fill=Chess.color[c1])

    def clicked(self, e):
        x, y = Chess.coords_to_grid(e.x, e.y)
        k = 10 * x + y
        coord = self.isClicked

        if k == coord:
            self.secondClick = k
        else:
            self.secondClick = None
            if coord != None:
                self.set(coord, 'normal')

            if self.board[k] != None:
                self.set(k, 'select')
                self.isClicked = k
            else:
                self.isClicked = None
                return

        #Selection mechanism
        self.isHover = k
        self.canvas.tag_raise(self.board[self.isClicked].img_id)
        self.set(k, 'button')
        self.move_obj(self.board[self.isClicked], e.x, e.y)

    def released(self, e):
        #print(e.x, e.y)
        if self.isClicked == None:
            return

        x1, y1, x2, y2 = Chess.grid_to_coords(self.isClicked)
        self.move_obj(self.board[self.isClicked], (x1 + x2) // 2,
                      (y1 + y2) // 2)

        if self.secondClick != None:
            if self.isHover == self.isClicked:
                self.isClicked = None
                self.set(self.isHover, 'normal')
        else:
            pass

        self.set(self.isHover, 'normal', preserve_select=True)
        self.isHover = None

    def drag_piece(self, e):

        if self.isClicked == None:
            return

        x, y = self.coords_to_grid(e.x, e.y)
        k = x * 10 + y

        if self.isHover != (k):
            if self.isHover != None:
                self.set(self.isHover, 'normal', preserve_select=True)
                self.set(k, 'button')

            else:
                self.set(k, 'button')

            self.isHover = k

        self.move_obj(self.board[self.isClicked], e.x, e.y)

    def move_obj(self, obj, x, y):
        self.canvas.moveto(obj.img_id, x - obj.i.width() // 2,
                           y - obj.i.height() // 2)

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


if __name__ == '__main__':
    app = Chess()
    app.mainloop()