import tkinter as tk
import tkinter.ttk as ttk
import random
import threading
import os
from tkinter import messagebox
from PIL import ImageTk, Image, ImageOps
from time import sleep

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
from pygame import mixer

mixer.init()  # pygame music player initialise


class Monopoly(tk.Toplevel):
    def __init__(self):  # playerdetails, me, propertydetails
        super().__init__()
        self.create_window()
        self.create_gui_divisions()
        self.create_image_obj()
        self.dice_tokens()

        self.property_frame = None
        self.board_canvas.bind("<Button-1>", self.property_click)

        # Random
        self.player_color = "red"
        self.owner = "Player 1"
        self.houses = 0  # [-1 to 5]

        self.owner_stations_owned = 2
        self.owner_utilities_owned = 1

        self.dictionary = {
            0: ["player1", self.red_token, 0],
            1: ["player2", self.green_token, 0],
            2: ["player3", self.blue_token, 0],
            3: ["player4", self.yellow_token, 0],
        }
        self.check, self.player = 0, []
        self.injail = False
        # END Random

        # DATABASE STUFF, temporary random variables for now
        self.d = {}
        self.d["Mayfair"] = dict(
            zip(
                [
                    "Rent",
                    "With Color Set",
                    "With 1 House",
                    "With 2 Houses",
                    "With 3 Houses",
                    "With 4 Houses",
                    "With Hotel",
                    "Mortgage Value",
                    "House Cost",
                    "Hotel Cost",
                ],
                [50, 100, 200, 600, 1400, 1700, 2000, 200, 200, 200],
            )
        )
        self.property_color = "#016cbf"

    def create_window(self):
        screen_width = int(0.9 * self.winfo_screenwidth())
        screen_height = int(screen_width / 1.9)
        x_coord = self.winfo_screenwidth() // 2 - screen_width // 2
        y_coord = (self.winfo_screenheight() - 70) // 2 - screen_height // 2

        self.board_side = screen_height - 65  # Length of board
        self.property_width = self.board_side / 12.2  # Width of one property on board

        self.title("Monopoly")
        self.resizable(False, False)
        self.geometry(f"{screen_width}x{screen_height}+{x_coord}+{y_coord}")
        self.config(bg="white")
        self.protocol("WM_DELETE_WINDOW", root.destroy)
        # Withdrawing Monopoly screen initially, to show only when game starts
        self.withdraw()

    def create_gui_divisions(self):

        self.board_canvas = tk.Canvas(
            self, width=self.board_side, height=self.board_side
        )
        self.board_canvas.place(relx=0.01, rely=0.04, anchor="nw")

        self.main_frame = tk.Frame(
            self,
            width=self.board_side - 2,
            height=self.board_side - 2,
            background="white",
        )
        self.main_frame.place(relx=0.99, rely=0.04, anchor="ne")

    def start_monopoly(self):  # Starting Game, withdrawing start window
        self.deiconify()
        root.withdraw()

    def create_image_obj(self):
        self.board_image = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open("Assets/BoardIMG.jpg").resize(
                    (self.board_side, self.board_side), Image.Resampling.LANCZOS
                )
            )
        )
        self.board_canvas.create_image(2, 2, image=self.board_image, anchor="nw")

        self.info_tag = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open("Assets/big_info.png").resize(
                    (int(self.property_width / 2), int(self.property_width / 2)),
                    Image.Resampling.LANCZOS,
                )
            )
        )

        self.station_image = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open("Assets/station.png").resize(
                    (int(2.5 * self.property_width), int(2.5 * self.property_width)),
                    Image.Resampling.LANCZOS,
                )
            )
        )

        self.water_image = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open("Assets/water.png").resize(
                    (int(2.5 * self.property_width), int(2 * self.property_width)),
                    Image.Resampling.LANCZOS,
                )
            )
        )

        self.electric_image = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open("Assets/electric.png").resize(
                    (int(2 * self.property_width), int(2.25 * self.property_width)),
                    Image.Resampling.LANCZOS,
                )
            )
        )

        self.dice1 = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open("Assets/dice1.png").resize(
                    (int(0.9 * self.property_width), int(0.9 * self.property_width)),
                    Image.Resampling.LANCZOS,
                )
            )
        )
        self.dice2 = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open("Assets/dice2.png").resize(
                    (int(0.9 * self.property_width), int(0.9 * self.property_width)),
                    Image.Resampling.LANCZOS,
                )
            )
        )
        self.dice3 = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open("Assets/dice3.png").resize(
                    (int(0.9 * self.property_width), int(0.9 * self.property_width)),
                    Image.Resampling.LANCZOS,
                )
            )
        )
        self.dice4 = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open("Assets/dice4.png").resize(
                    (int(0.9 * self.property_width), int(0.9 * self.property_width)),
                    Image.Resampling.LANCZOS,
                )
            )
        )
        self.dice5 = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open("Assets/dice5.png").resize(
                    (int(0.9 * self.property_width), int(0.9 * self.property_width)),
                    Image.Resampling.LANCZOS,
                )
            )
        )
        self.dice6 = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open("Assets/dice6.png").resize(
                    (int(0.9 * self.property_width), int(0.9 * self.property_width)),
                    Image.Resampling.LANCZOS,
                )
            )
        )

        self.red_token_image = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open("Assets/red.png").resize(
                    (self.board_side // 39, self.board_side // 39),
                    Image.Resampling.LANCZOS,
                )
            )
        )
        self.green_token_image = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open("Assets/green.png").resize(
                    (self.board_side // 39, self.board_side // 39),
                    Image.Resampling.LANCZOS,
                )
            )
        )
        self.blue_token_image = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open("Assets/blue.png").resize(
                    (self.board_side // 39, self.board_side // 39),
                    Image.Resampling.LANCZOS,
                )
            )
        )
        self.yellow_token_image = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open("Assets/yellow.png").resize(
                    (self.board_side // 39, self.board_side // 39),
                    Image.Resampling.LANCZOS,
                )
            )
        )

    def dice_tokens(self):
        self.die_dict = dict(
            zip(
                (1, 2, 3, 4, 5, 6),
                (
                    self.dice1,
                    self.dice2,
                    self.dice3,
                    self.dice4,
                    self.dice5,
                    self.dice6,
                ),
            )
        )

        button_style = ttk.Style()
        button_style.configure(
            "my.TButton", font=("times", int(self.property_width / 3))
        )

        roll_button = ttk.Button(
            self.board_canvas,
            text="Roll Dice",
            style="my.TButton",
            command=lambda: self.roll_dice(),
        )
        roll_button.place(relx=0.5, rely=0.5, anchor="center")

        self.dice_spot1 = tk.Label(
            self.board_canvas, image=self.dice5, border=0, highlightthickness=0
        )
        self.dice_spot1.place(relx=0.485, rely=0.46, anchor="se")

        self.dice_spot2 = tk.Label(
            self.board_canvas, image=self.dice5, border=0, highlightthickness=0
        )
        self.dice_spot2.place(relx=0.515, rely=0.46, anchor="sw")

        self.red_token = tk.Button(
            self.board_canvas,
            image=self.red_token_image,
            border=0,
            highlightthickness=0,
            command=lambda: self.player_frame_popup("Player 1"),
        )
        self.red_token.place(
            x=self.board_side - 1.2 * self.property_width,
            y=self.board_side - 0.75 * self.property_width,
            anchor="center",
        )

        self.green_token = tk.Button(
            self.board_canvas,
            image=self.green_token_image,
            border=0,
            highlightthickness=0,
            command=lambda: self.player_frame_popup("Player 2"),
        )
        self.green_token.place(
            x=self.board_side - 0.85 * self.property_width,
            y=self.board_side - 0.75 * self.property_width,
            anchor="center",
        )

        self.blue_token = tk.Button(
            self.board_canvas,
            image=self.blue_token_image,
            border=0,
            highlightthickness=0,
            command=lambda: self.player_frame_popup("Player 3"),
        )
        self.blue_token.place(
            x=self.board_side - 1.2 * self.property_width,
            y=self.board_side - 0.4 * self.property_width,
            anchor="center",
        )

        self.yellow_token = tk.Button(
            self.board_canvas,
            image=self.yellow_token_image,
            border=0,
            highlightthickness=0,
            command=lambda: self.player_frame_popup("Player 4"),
        )
        self.yellow_token.place(
            x=self.board_side - 0.85 * self.property_width,
            y=self.board_side - 0.4 * self.property_width,
            anchor="center",
        )

    def hotel_rules(self):
        messagebox.showinfo("HOTEL RULES", "HOTEL RULES")

    def station_rules(self):
        messagebox.showinfo("STATION RULES", "STATION RULES")

    def utility_rules(self):
        messagebox.showinfo("UTILITY RULES", "UTILITY RULES")

    def jail_rules(self):
        messagebox.showinfo("JAIL RULES", "JAIL RULES")

    def property_frame_popup(self, property):
        if self.property_frame:
            self.delete_property_frame()
        self.property_frame = tk.Frame(
            self.main_frame,
            width=(self.board_side - 2) // 2.05,
            height=(self.board_side - 2) // 1.75,
            bg="#F9FBFF",
            highlightthickness=2,
            highlightbackground="black",
        )

        self.property_frame.place(relx=1, rely=1, anchor="se")

        if "station" in property.lower():
            station_label = tk.Label(
                self.property_frame,
                image=self.station_image,
                border=0,
                highlightthickness=0,
            )
            station_label.place(relx=0.5, rely=0.2, anchor="center")

            tk.Label(
                self.property_frame,
                text=property.upper(),
                font=("times", (self.board_side - 2) // 40),
                bg="#F9FBFF",
            ).place(relx=0.5, rely=0.4, anchor="center")

            tk.Button(
                self.property_frame,
                text="✕",
                font=("courier", (self.board_side - 2) // 60),
                bg="#F9FBFF",
                highlightthickness=0,
                border=0,
                activebackground="#F9FBFF",
                command=self.delete_property_frame,
            ).place(relx=0.95, rely=0.05, anchor="ne")

            canvas = tk.Canvas(
                self.property_frame,
                highlightthickness=0,
                width=(self.board_side - 2) // 2.25,
                height=(self.board_side - 2) // 4,
                bg="#F9FBFF",
            )
            canvas.place(relx=0.5, rely=0.725, anchor="center")
            canvas.update()
            y_coord = canvas.winfo_height() / 10

            ttk.Separator(canvas, orient="horizontal").place(
                relx=0.5, rely=0.8, anchor="center", relwidth=0.8
            )

            tk.Label(
                self.property_frame,
                text=f"Owner: {self.owner}",
                font=("times", (self.board_side - 2) // 46),
                fg=self.player_color,
                bg="#F9FBFF",
            ).place(relx=0.5, rely=0.475, anchor="center")

            tk.Button(
                self.property_frame,
                image=self.big_info_tag,
                border=0,
                highlightthickness=0,
                command=self.station_rules,
            ).place(x=35, rely=0.9, anchor="center")

            row_counter = 0
            stations_data = {
                "Rent": 25,
                "If 2 Stations are owned": 50,
                "If 3 Stations are owned": 100,
                "If 4 Stations are owned": 200,
                "Mortgage Value": 100,
            }
            for (
                i,
                j,
            ) in stations_data.items():  # Placing and formatting Rent data on card
                row_counter += 1
                if row_counter == self.owner_stations_owned:
                    canvas.create_text(
                        2,
                        y_coord - 2,
                        anchor="w",
                        text="▶",
                        font=("times", (self.board_side - 2) // 32),
                        fill=self.player_color,
                    )
                if row_counter == 5:  # mortgage
                    canvas.create_text(
                        45,
                        y_coord,
                        anchor="w",
                        text=i,
                        font=("times", (self.board_side - 2) // 51),
                    )
                    canvas.create_text(
                        canvas.winfo_width() / 1.3,
                        y_coord,
                        text="₩",
                        angle=180,
                        font=("courier", (self.board_side - 2) // 51),
                    )
                    canvas.create_text(
                        canvas.winfo_width() - 35,
                        y_coord,
                        anchor="e",
                        text=str(j),
                        font=("times", (self.board_side - 2) // 51),
                    )
                else:
                    canvas.create_text(
                        25,
                        y_coord,
                        anchor="w",
                        text=i,
                        font=("times", (self.board_side - 2) // 45),
                    )
                    canvas.create_text(
                        canvas.winfo_width() / 1.3,
                        y_coord,
                        text="₩",
                        angle=180,
                        font=("courier", (self.board_side - 2) // 45),
                    )
                    canvas.create_text(
                        canvas.winfo_width() - 25,
                        y_coord,
                        anchor="e",
                        text=str(j),
                        font=("times", (self.board_side - 2) // 45),
                    )

                y_coord += canvas.winfo_height() / 5

        elif any([a in property.lower() for a in ["water", "electric"]]):
            if "water" in property.lower():
                utility_image = self.water_image
            else:
                utility_image = self.electric_image
            utility_label = tk.Label(
                self.property_frame, image=utility_image, border=0, highlightthickness=0
            )
            utility_label.place(relx=0.5, rely=0.2, anchor="center")

            tk.Label(
                self.property_frame,
                text=property.upper(),
                font=("times", (self.board_side - 2) // 40),
                bg="#F9FBFF",
            ).place(relx=0.5, rely=0.4, anchor="center")

            tk.Button(
                self.property_frame,
                text="✕",
                font=("courier", (self.board_side - 2) // 60),
                bg="#F9FBFF",
                highlightthickness=0,
                border=0,
                activebackground="#F9FBFF",
                command=self.delete_property_frame,
            ).place(relx=0.95, rely=0.05, anchor="ne")

            canvas = tk.Canvas(
                self.property_frame,
                highlightthickness=0,
                width=(self.board_side - 2) // 2.25,
                height=(self.board_side - 2) // 4,
                bg="#F9FBFF",
            )
            canvas.place(relx=0.5, rely=0.725, anchor="center")
            canvas.update()
            y_coord = canvas.winfo_height() / 12

            ttk.Separator(canvas, orient="horizontal").place(
                relx=0.5, rely=0.85, anchor="center", relwidth=0.8
            )

            tk.Label(
                self.property_frame,
                text=f"Owner: {self.owner}",
                font=("times", (self.board_side - 2) // 46),
                fg=self.player_color,
                bg="#F9FBFF",
            ).place(relx=0.5, rely=0.475, anchor="center")

            tk.Button(
                self.property_frame,
                image=self.big_info_tag,
                border=0,
                highlightthickness=0,
                command=self.utility_rules,
            ).place(x=35, rely=0.925, anchor="center")

            row_counter = 0
            try:  # if dice has been rolled
                utilities_data = {
                    f"Rent based on last roll ({self.current_move}),": None,
                    "If 1 utility is owned:": None,
                    f" 4   x  {self.current_move}     = ": 4 * self.current_move,
                    "If 2 utilities are owned:": None,
                    f"10  x  {self.current_move}     =": 10 * self.current_move,
                    "Mortgage Value": 75,
                }
            except:  # if dice has not been rolled yet
                utilities_data = {
                    "Rent based on roll (10),": None,
                    "If 1 utility is owned:": None,
                    f" 4   x  10     = ": 40,
                    "If 2 utilities are owned:": None,
                    f"10  x  10     =": 100,
                    "Mortgage Value": 75,
                }
            for (
                i,
                j,
            ) in utilities_data.items():  # Placing and formatting Rent data on card
                row_counter += 1
                if row_counter == self.owner_utilities_owned * 2:
                    canvas.create_text(
                        2,
                        y_coord - 2,
                        anchor="w",
                        text="▶",
                        font=("times", (self.board_side - 2) // 32),
                        fill=self.player_color,
                    )
                if row_counter in [1, 2, 4]:  # text row
                    canvas.create_text(
                        25,
                        y_coord,
                        anchor="w",
                        text=i,
                        font=("times", (self.board_side - 2) // 45),
                    )
                elif row_counter in [3, 5]:  # rent row
                    canvas.create_text(
                        canvas.winfo_width() / 2.75,
                        y_coord,
                        anchor="w",
                        text=i,
                        font=("times", (self.board_side - 2) // 45),
                    )
                    canvas.create_text(
                        canvas.winfo_width() / 1.3,
                        y_coord,
                        text="₩",
                        angle=180,
                        font=("courier", (self.board_side - 2) // 45),
                    )
                    canvas.create_text(
                        canvas.winfo_width() - 25,
                        y_coord,
                        anchor="e",
                        text=str(j),
                        font=("times", (self.board_side - 2) // 45),
                    )
                elif row_counter == 6:  # mortgage
                    canvas.create_text(
                        45,
                        y_coord * 1.025,
                        anchor="w",
                        text=i,
                        font=("times", (self.board_side - 2) // 51),
                    )
                    canvas.create_text(
                        canvas.winfo_width() / 1.3,
                        y_coord * 1.025,
                        text="₩",
                        angle=180,
                        font=("courier", (self.board_side - 2) // 51),
                    )
                    canvas.create_text(
                        canvas.winfo_width() - 35,
                        y_coord * 1.025,
                        anchor="e",
                        text=str(j),
                        font=("times", (self.board_side - 2) // 51),
                    )

                y_coord += canvas.winfo_height() / 6

        else:
            title_frame = tk.Frame(
                self.property_frame,
                width=(self.board_side - 2) // 2.25,
                height=(self.board_side - 2) // 10,
                bg=self.property_color,
                highlightthickness=2,
                highlightbackground="black",
            )
            title_frame.place(relx=0.5, rely=0.125, anchor="center")

            tk.Label(
                title_frame,
                text="TITLE DEED",
                font=("times", (self.board_side - 2) // 56),
                bg=self.property_color,
            ).place(relx=0.5, rely=0.25, anchor="center")

            tk.Label(
                title_frame,
                text=property.upper(),
                font=("times", (self.board_side - 2) // 40),
                bg=self.property_color,
            ).place(relx=0.5, rely=0.65, anchor="center")

            tk.Button(
                title_frame,
                text="✕",
                font=("courier", (self.board_side - 2) // 60),
                bg=self.property_color,
                highlightthickness=0,
                border=0,
                activebackground=self.property_color,
                command=self.delete_property_frame,
            ).place(relx=1, rely=0, anchor="ne")

            canvas = tk.Canvas(
                self.property_frame,
                highlightthickness=0,
                width=(self.board_side - 2) // 2.25,
                height=(self.board_side - 2) // 2.6,
                bg="#F9FBFF",
            )
            canvas.place(relx=0.5, rely=0.625, anchor="center")
            canvas.update()
            y_coord = canvas.winfo_height() / 21

            ttk.Separator(canvas, orient="horizontal").place(
                relx=0.5, rely=0.69, anchor="center", relwidth=0.8
            )

            tk.Label(
                self.property_frame,
                text=f"Owner: {self.owner}",
                font=("times", (self.board_side - 2) // 46),
                fg=self.player_color,
                bg="#F9FBFF",
            ).place(relx=0.5, rely=0.25, anchor="center")

            tk.Button(
                self.property_frame,
                image=self.info_tag,
                border=0,
                highlightthickness=0,
                command=self.hotel_rules,
            ).place(x=35, rely=0.9, anchor="center")

            row_counter = -2
            for i, j in self.d[
                property
            ].items():  # Placing and formatting Rent data on card
                row_counter += 1
                if row_counter == self.houses:
                    canvas.create_text(
                        2,
                        y_coord - 2,
                        anchor="w",
                        text="▶",
                        font=("times", (self.board_side - 2) // 32),
                        fill=self.player_color,
                    )
                if row_counter in [-1, 0]:  # rent, double rent
                    canvas.create_text(
                        25,
                        y_coord,
                        anchor="w",
                        text=i,
                        font=("times", (self.board_side - 2) // 42),
                    )
                    canvas.create_text(
                        canvas.winfo_width() / 1.375,
                        y_coord,
                        text="₩",
                        angle=180,
                        font=("courier", (self.board_side - 2) // 42),
                    )
                    canvas.create_text(
                        canvas.winfo_width() - 25,
                        y_coord,
                        anchor="e",
                        text=str(j),
                        font=("times", (self.board_side - 2) // 42),
                    )
                elif row_counter in [1, 2, 3, 4]:  # houses
                    canvas.create_text(
                        25,
                        y_coord,
                        anchor="w",
                        text=i,
                        font=("times", (self.board_side - 2) // 42),
                        fill="green",
                    )
                    canvas.create_text(
                        canvas.winfo_width() / 1.375,
                        y_coord,
                        text="₩",
                        angle=180,
                        font=("courier", (self.board_side - 2) // 42),
                        fill="green",
                    )
                    canvas.create_text(
                        canvas.winfo_width() - 25,
                        y_coord,
                        anchor="e",
                        text=str(j),
                        font=("times", (self.board_side - 2) // 42),
                        fill="green",
                    )
                elif row_counter == 5:  # hotel
                    canvas.create_text(
                        25,
                        y_coord,
                        anchor="w",
                        text=i,
                        font=("times", (self.board_side - 2) // 42),
                        fill="red",
                    )
                    canvas.create_text(
                        canvas.winfo_width() / 1.375,
                        y_coord,
                        text="₩",
                        angle=180,
                        font=("courier", (self.board_side - 2) // 42),
                        fill="red",
                    )
                    canvas.create_text(
                        canvas.winfo_width() - 25,
                        y_coord,
                        anchor="e",
                        text=str(j),
                        font=("times", (self.board_side - 2) // 42),
                        fill="red",
                    )
                elif row_counter == 6:  # mortgage
                    canvas.create_text(
                        45,
                        y_coord,
                        anchor="w",
                        text=i,
                        font=("times", (self.board_side - 2) // 49),
                    )
                    canvas.create_text(
                        canvas.winfo_width() / 1.375,
                        y_coord,
                        text="₩",
                        angle=180,
                        font=("courier", (self.board_side - 2) // 49),
                    )
                    canvas.create_text(
                        canvas.winfo_width() - 35,
                        y_coord,
                        anchor="e",
                        text=str(j),
                        font=("times", (self.board_side - 2) // 49),
                    )
                elif row_counter == 7:  # build house
                    canvas.create_text(
                        45,
                        y_coord,
                        anchor="w",
                        text=i,
                        font=("times", (self.board_side - 2) // 49),
                        fill="green",
                    )
                    canvas.create_text(
                        canvas.winfo_width() / 1.375,
                        y_coord,
                        text="₩",
                        angle=180,
                        font=("courier", (self.board_side - 2) // 49),
                        fill="green",
                    )
                    canvas.create_text(
                        canvas.winfo_width() - 35,
                        y_coord,
                        anchor="e",
                        text=str(j),
                        font=("times", (self.board_side - 2) // 49),
                        fill="green",
                    )
                elif row_counter == 8:  # build hotel
                    canvas.create_text(
                        45,
                        y_coord,
                        anchor="w",
                        text=i,
                        font=("times", (self.board_side - 2) // 49),
                        fill="red",
                    )
                    canvas.create_text(
                        canvas.winfo_width() / 1.375,
                        y_coord,
                        text="₩",
                        angle=180,
                        font=("courier", (self.board_side - 2) // 49),
                        fill="red",
                    )
                    canvas.create_text(
                        canvas.winfo_width() - 35,
                        y_coord,
                        anchor="e",
                        text=str(j),
                        font=("times", (self.board_side - 2) // 49),
                        fill="red",
                    )

                y_coord += canvas.winfo_height() / 10.25

    def delete_property_frame(self):
        self.property_frame.place_forget()
        self.property_frame = None

    def property_click(self, event):
        if event.x in range(0, 200) and event.y in range(0, 200):
            print("blah")
            self.property_frame_popup("Mayfair")

    def player_frame_popup(self, player):
        player_frame = tk.Frame(
            self.main_frame,
            width=(self.board_side - 2) // 2.05,
            height=(self.board_side - 2) // 2.45,
        )

        player_frame.place(relx=1, rely=0, anchor="ne")

    def bank_frame_popup(self):
        bank_frame = tk.Frame(
            self.main_frame,
            width=(self.board_side - 2) // 2.05,
            height=(self.board_side - 2) // 2.45,
        )

        bank_frame.place(relx=0, rely=0, anchor="nw")

    def action_frame_popup(self, action):
        action_frame = tk.Frame(
            self.main_frame,
            width=(self.board_side - 2) // 2.05,
            height=(self.board_side - 2) // 1.75,
        )

        action_frame.place(relx=0, rely=1, anchor="sw")

    def roll_dice(self):
        player = self.dictionary[self.check % 4]
        mixer.music.load("Assets/diceroll.mp3")
        mixer.music.play(loops=0)
        dice_roll = random.randint(1, 6), random.randint(1, 6)
        for i in range(18):
            self.dice_spot1.configure(image=self.die_dict[random.randint(1, 6)])
            self.dice_spot2.configure(image=self.die_dict[random.randint(1, 6)])
            self.dice_spot1.update()
            self.dice_spot2.update()
            sleep(0.12)
        self.dice_spot1.configure(image=self.die_dict[dice_roll[0]])
        self.dice_spot2.configure(image=self.die_dict[dice_roll[1]])
        self.current_move = sum(dice_roll)
        # self.move_token(self.current_move)
        print(f"MOVED {self.current_move}")
        self.check += 1


# scroll = ttk.Scrollbar(dataframe,orient=tk.VERTICAL)
# scroll.place(relx=1,rely=0,anchor='ne',relheight=1)
# scroll.config(command=listbox.yview)

# TODO: Make Thread to update all frames, based on game progress

root = tk.Tk()
mono = Monopoly()
mono.start_monopoly()
root.mainloop()
