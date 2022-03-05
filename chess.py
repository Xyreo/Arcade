import tkinter as tk
from PIL import Image, ImageTk, ImageOps
import os


class Pieces:

    types = ['BLANK', 'ROOK', 'KING', 'QUEEN', 'BISHOP', 'KNIGHT', 'PAWN']

    @staticmethod
    def initialise():
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

        return board

    def __init__(self, piece='BLANK', color='NONE'):
        self.piece = piece
        self.color = color

    def img(self):

        if self.color == 'NONE':
            return None

        size = 100
        path = os.path.join('Chess_Assets', 'PNGs', 'With shadow', '128px')
        p = os.path.join(path, (self.color[0] + '_' + self.piece +
                                '_png_shadow_128px' + '.png').lower())

        return ImageTk.PhotoImage(Image.open(p))

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


class Chess(tk.Tk):

    def __init__(self):
        super().__init__()
        self.geometry("600x600")
        self.board = []
        self.board_pieces = Pieces.initialise()

        for i in range(8):
            l = []
            for j in range(8):
                button = tk.Button(
                    self,
                    command=lambda n=(i * 8) + j: self.button_handler(n),
                    height=4,
                    width=8,
                    border=1,
                    bg='WHITE' if not (i + j) % 2 else 'BLACK',
                    image=self.board_pieces[i][j].img(),
                    text=self.board_pieces[i][j].piece)
                button.grid(column=j, row=i)
                l.append(button)
            self.board.append(l)

    def button_handler(self, n):
        i, j = n // 8, n % 8
        print(i, ' ', j)
        self.board[i][j].configure(bg='RED', state='disabled')


if __name__ == '__main__':
    app = Chess()
    app.mainloop()