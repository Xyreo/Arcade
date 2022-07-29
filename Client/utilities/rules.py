import tkinter as tk
import sys
import os
import typing


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
MONOPOLY_ASSETS = os.path.join(ASSET, "mnply_assets")
CHESS_ASSETS = os.path.join(ASSET, "chess_assets")


class Rules(tk.Toplevel):
    def __init__(self, type: typing.Literal["Arcade", "Chess", "Monopoly"]):
        super().__init__()

        self.screen_width = int(0.9 * self.winfo_screenwidth())
        self.screen_height = int(self.screen_width / 1.9)
        self.x_coord = self.winfo_screenwidth() // 2 - self.screen_width // 2
        self.y_coord = (self.winfo_screenheight() - 70) // 2 - self.screen_height // 2

        self.title(type + " Rules and Information")
        self.geometry(
            f"{self.screen_width//2}x{self.screen_height}+{self.x_coord+self.screen_width//4}+{self.y_coord}"
        )
        self.iconbitmap(os.path.join(HOME_ASSETS, "icon.ico"))

        self.txt_widget = tk.Text(self, font=("arial", 13), wrap="word")
        self.txt_widget.place(relx=0, rely=0, relheight=1, relwidth=1, anchor="nw")
        d = {"Arcade": HOME_ASSETS, "Chess": CHESS_ASSETS, "Monopoly": MONOPOLY_ASSETS}
        with open(os.path.join(d[type], "rules.txt")) as f:
            self.txt_widget.insert("end", f.read())
            self.txt_widget.configure(state="disabled")
