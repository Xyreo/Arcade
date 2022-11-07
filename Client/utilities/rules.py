import os
import sys
import tkinter as tk
import typing
import webbrowser


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
    def __init__(self, master, type: typing.Literal["Arcade", "Chess", "Monopoly"]):
        super().__init__(master)
        self.rule_windows = [
            i for i in master.winfo_children() if "rules" in str(i.winfo_name())
        ]
        while len(self.rule_windows) > 1:
            self.rule_windows[0].destroy()
            self.rule_windows.pop(0)

        self.screen_width = int(0.9 * self.winfo_screenwidth())
        self.screen_height = int(self.screen_width / 1.9)
        self.x_coord = self.winfo_screenwidth() // 2 - int(self.screen_width / 3.2)
        self.y_coord = (self.winfo_screenheight() - 70) // 2 - self.screen_height // 2
        self.geometry(
            f"{int(self.screen_width/1.6)}x{self.screen_height}+{self.x_coord}+{self.y_coord}"
        )

        self.title(type + " Rules and Information")
        self.iconbitmap(os.path.join(HOME_ASSETS, "icon.ico"))

        d = {"Arcade": HOME_ASSETS, "Chess": CHESS_ASSETS, "Monopoly": MONOPOLY_ASSETS}

        self.txt_widget = tk.Text(
            self,
            font=("arial", 13),
            wrap="word",
            tabstyle="wordprocessor",
            spacing1=5,
            spacing2=3,
            spacing3=10,
            padx=20,
            pady=20,
        )
        self.txt_widget.place(relx=0, rely=0, relheight=1, relwidth=1, anchor="nw")

        self.txt_widget.tag_config("bold", font=("arial", 13, "bold"))
        self.txt_widget.tag_config("italic", font=("arial", 13, "italic"))
        self.txt_widget.tag_config("link", foreground="#15a8cd", underline=1)
        self.txt_widget.tag_bind(
            "link", "<Enter>", lambda e: self.txt_widget.config(cursor="hand2")
        )
        self.txt_widget.tag_bind(
            "link", "<Leave>", lambda e: self.txt_widget.config(cursor="")
        )

        with open(os.path.join(d[type], "rules.txt")) as f:
            self.txt_widget.insert("end", f.read())
            if type == "Chess":
                self.txt_widget.tag_add("link", "1.14", "1.18")
                self.txt_widget.tag_bind(
                    "link",
                    "<Button-1>",
                    lambda e: webbrowser.open_new_tab(
                        "https://raw.githubusercontent.com/Chaitanya-Keyal/Arcade/main/Client/assets/chess_assets/basic_rules.pdf"
                    ),
                )
                self.txt_widget.tag_add(
                    "bold",
                    "1.0",
                    "1.1000",
                    "2.0",
                    "2.1000",
                    "6.0",
                    "6.1000",
                    "12.0",
                    "12.1000",
                    "20.0",
                    "20.1000",
                    "23.0",
                    "23.1000",
                )
            elif type == "Monopoly":
                self.txt_widget.tag_add(
                    "bold",
                    "1.0",
                    "1.1000",
                    "4.0",
                    "4.1000",
                    "6.0",
                    "6.1000",
                    "10.0",
                    "10.1000",
                    "13.0",
                    "13.1000",
                    "16.0",
                    "16.1000",
                    "21.0",
                    "21.1000",
                    "24.0",
                    "24.1000",
                    "26.0",
                    "26.1000",
                    "31.0",
                    "31.1000",
                    "33.0",
                    "33.1000",
                    "40.0",
                    "40.1000",
                    "45.0",
                    "45.1000",
                    "53.0",
                    "53.1000",
                    "59.0",
                    "59.1000",
                )
            else:
                self.txt_widget.tag_add("bold", "1.0", "1.1000")
                self.txt_widget.tag_add("italic", "2.29", "2.35", "2.39", "2.48")
                self.txt_widget.tag_add("link", "18.93", "18.97")
                self.txt_widget.tag_bind(
                    "link",
                    "<Button-1>",
                    lambda e: webbrowser.open_new_tab(
                        "https://github.com/Chaitanya-Keyal/Arcade/discussions"
                    ),
                )
            self.txt_widget.configure(state="disabled")
