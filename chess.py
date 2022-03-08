import tkinter as tk
from PIL import Image, ImageTk, ImageOps
import os


class Pieces:

    types = ['BLANK', 'ROOK', 'KING', 'QUEEN', 'BISHOP', 'KNIGHT', 'PAWN']
    images = {}

    @staticmethod
    def initialise(f):
        board = [[Pieces() for j in range(8)] for i in range(8)]
        board[0] = [
            Pieces('ROOK', 'BLACK'),
            Pieces('KNIGHT', 'BLACK'),
            Pieces('BISHOP', 'BLACK'),
            Pieces('QUEEN', 'BLACK'),
            Pieces('KING', 'BLACK'),
            Pieces('BISHOP', 'BLACK'),
            Pieces('KNIGHT', 'BLACK'),
            Pieces('ROOK', 'BLACK')
        ]
        board[7] = [
            Pieces('ROOK', 'WHITE'),
            Pieces('KNIGHT', 'WHITE'),
            Pieces('BISHOP', 'WHITE'),
            Pieces('QUEEN', 'WHITE'),
            Pieces('KING', 'WHITE'),
            Pieces('BISHOP', 'WHITE'),
            Pieces('KNIGHT', 'WHITE'),
            Pieces('ROOK', 'WHITE')
        ]
        board[1] = [Pieces('PAWN', 'BLACK') for i in range(8)]
        board[6] = [Pieces('PAWN', 'WHITE') for i in range(8)]
        Pieces.images = {('BLACK' + i): Pieces.img('black', i, f)
                         for i in Pieces.types}

        Pieces.images.update({('WHITE' + i): Pieces.img('white', i, f)
                              for i in Pieces.types})

        Pieces.images['NONEBLANK'] = Pieces.img('none', 'BLANK', f)
        #print(Pieces.images)

        return board

    def __init__(self, piece='BLANK', color='NONE'):
        self.piece = piece
        self.color = color

    def move(self, board):
        pass

    def rook_move(self, board):
        pass

    def king_move(self, board):
        pass

    def queen_move(self, board):
        pass

    def bishop_move(self, board):
        pass

    def knight_move(self, board):
        pass

    def bishop_move(self, board):
        pass

    @staticmethod
    def img(color, piece, f):
        path = os.path.join('Chess_Assets', '128h')
        if piece == 'BLANK':
            p = os.path.join(path, 'blank.png')

        else:
            i = (color[0] + '_' + piece + '_png_128px' + '.png').lower()
            p = os.path.join(path, i)

        size = f.winfo_width() * 8 // 80
        #print(size)
        return ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open(p).resize((size * 95 // 100, size),
                                     Image.ANTIALIAS)))


class Chess(tk.Tk):

    def __init__(self):
        super().__init__()
        self.size = str(self.winfo_screenheight() * 4 // 5)
        self.geometry(f'{self.size}x{self.size}')
        self.board = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.frame = tk.Frame(self)
        self.frame.grid(sticky=tk.NSEW)
        self.frame.grid_columnconfigure(tuple(range(8)), weight=1)
        self.frame.grid_rowconfigure(tuple(range(8)), weight=1)
        self.frame.update()
        self.board_pieces = Pieces.initialise(self.frame)
        p = os.path.join('Chess_Assets', 'board')
        self.boardimg = {'WHITE': '#bacbe6', 'BLACK': '#617bed'}

        for i in range(8):
            l = []

            for j in range(8):
                button = tk.Button(
                    self.frame,
                    command=lambda n=(i * 8) + j: self.button_handler(n),
                    height=128,
                    width=128,
                    border=0,
                    background=self.boardimg['WHITE']
                    if not (i + j) % 2 else self.boardimg['BLACK'],
                    activebackground=self.boardimg['WHITE']
                    if not (i + j) % 2 else self.boardimg['BLACK'],
                    text=self.board_pieces[i][j].piece,
                )

                button.grid(column=j, row=i, sticky=tk.NSEW)
                l.append(button)
            self.board.append(l)

        for i in range(8):
            for j in range(8):
                b = self.board[i][j]
                p = self.board_pieces[i][j]
                b.configure(image=Pieces.images[p.color + p.piece])
                pass

    def button_handler(self, n):
        i, j = n // 8, n % 8
        print(i, ' ', j)
        self.board[i][j].configure(
            bg='RED',
            #state=tk.DISABLED,
            command=0,
            disabledforeground=self.boardimg['WHITE']
            if not (i + j) % 2 else self.boardimg['BLACK'],
        )


if __name__ == '__main__':
    app = Chess()
    app.mainloop()