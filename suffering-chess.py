import tkinter as tk
import os
from PIL import ImageOps, Image, ImageTk


class Piece:

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
    color = {
        'black': '#eeeed2',
        'white': '#769656',
        'selected': '',
    }
    size = 0
    pieces = {}

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
        self.initialize_board()

    def initialize_board(self):

        self.grid_coords = {}
        self.grid = {}
        for i in range(8):
            for j in range(8):
                key = (i * 10) + j
                self.grid_coords[key] = ((Chess.size // 8) * i,
                                         (Chess.size // 8) * (i + 1),
                                         (Chess.size // 8) * j,
                                         (Chess.size // 8) * (j + 1))

        for key, value in self.grid_coords.items():

            self.grid[key] = self.canvas.create_rectangle(
                value[0],
                value[2],
                value[1],
                value[3],
                fill=Chess.color['white'] if
                (key // 10 + key % 10) % 2 else Chess.color['black'],
                outline='',
            )
            '''self.canvas.create_text((value[0] + value[1]) // 2,
                                    (value[2] + value[3]) // 2,
                                    anchor=tk.CENTER,
                                    text=str(key))'''


if __name__ == '__main__':
    app = Chess()
    app.mainloop()