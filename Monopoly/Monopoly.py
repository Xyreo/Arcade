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

# TODO: Change to pyaudio

import mysql.connector as msc

ASSET = "Monopoly/Assets"

db = msc.connect(
    host="167.71.231.52",
    username="project-work",
    password="mySQLpass",
    database="arcade",
)
cursor = db.cursor()


class Property:
    def __init__(self, position):
        cursor.execute(f"select * from monopoly_board_values where position={position}")
        details = list(cursor)[0]
        self.name = details[0]
        self.colour = details[2]
        self.hex = details[3]
        self.price = details[4]
        self.rent_values = [
            details[5],
            details[6],
            details[7],
            details[8],
            details[9],
            details[10],
            details[11],
        ]
        self.mortgage = details[12]
        self.build = details[13]

        self.owner = None
        self.houses = -1
        """
        No. of houses meaning:
        -1 : Rent
        0 : Rent with colour set
        1: Rent with 1 house
        2: Rent with 2 houses
        3: Rent with 3 houses
        4: Rent with 4 houses
        5: Rent with hotel
        """

    def rent(self):
        return self.rent_values[self.houses + 1]


class Monopoly(tk.Toplevel):
    def __init__(self, playerdetails, me):
        super().__init__()
        self.player_details = playerdetails
        self.me = me

        self.create_window()
        self.create_gui_divisions()
        self.initialise()
        self.create_image_obj()
        self.dice_tokens()

    def initialise(self):
        self.property_frame = None
        self.property_pos_displayed = None
        self.board_canvas.bind("<Button-1>", self.click_to_position)

        self.properties = {}
        for i in range(40):
            self.properties[i] = Property(i)

        for i in self.player_details:
            self.player_details[i].update(
                {"Money": 1500, "Injail": False, "Position": 0, "Properties": []}
            )  # Properties will store obj from properties dict

    def create_window(self):
        screen_width = int(0.9 * self.winfo_screenwidth())
        screen_height = int(screen_width / 1.9)
        x_coord = self.winfo_screenwidth() // 2 - screen_width // 2
        y_coord = (self.winfo_screenheight() - 70) // 2 - screen_height // 2

        self.board_side = int(screen_height * 0.9)  # Length of board
        self.property_width = self.board_side / 12.2  # Width of one property on board
        self.property_height = self.property_width * 1.6
        self.token_width = int(self.property_height * 0.176)

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
                Image.open(ASSET + "/BoardIMG.jpg").resize(
                    (self.board_side, self.board_side), Image.Resampling.LANCZOS
                )
            )
        )
        self.board_canvas.create_image(2, 2, image=self.board_image, anchor="nw")

        self.info_tag = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open(ASSET + "/big_info.png").resize(
                    (int(self.property_width / 2), int(self.property_width / 2)),
                    Image.Resampling.LANCZOS,
                )
            )
        )

        self.station_image = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open(ASSET + "/station.png").resize(
                    (int(2.5 * self.property_width), int(2.5 * self.property_width)),
                    Image.Resampling.LANCZOS,
                )
            )
        )

        self.water_image = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open(ASSET + "/water.png").resize(
                    (int(2.5 * self.property_width), int(2 * self.property_width)),
                    Image.Resampling.LANCZOS,
                )
            )
        )

        self.electric_image = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open(ASSET + "/electric.png").resize(
                    (int(2 * self.property_width), int(2.25 * self.property_width)),
                    Image.Resampling.LANCZOS,
                )
            )
        )

        self.dice1 = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open(ASSET + "/dice1.png").resize(
                    (int(0.9 * self.property_width), int(0.9 * self.property_width)),
                    Image.Resampling.LANCZOS,
                )
            )
        )
        self.dice2 = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open(ASSET + "/dice2.png").resize(
                    (int(0.9 * self.property_width), int(0.9 * self.property_width)),
                    Image.Resampling.LANCZOS,
                )
            )
        )
        self.dice3 = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open(ASSET + "/dice3.png").resize(
                    (int(0.9 * self.property_width), int(0.9 * self.property_width)),
                    Image.Resampling.LANCZOS,
                )
            )
        )
        self.dice4 = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open(ASSET + "/dice4.png").resize(
                    (int(0.9 * self.property_width), int(0.9 * self.property_width)),
                    Image.Resampling.LANCZOS,
                )
            )
        )
        self.dice5 = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open(ASSET + "/dice5.png").resize(
                    (int(0.9 * self.property_width), int(0.9 * self.property_width)),
                    Image.Resampling.LANCZOS,
                )
            )
        )
        self.dice6 = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open(ASSET + "/dice6.png").resize(
                    (int(0.9 * self.property_width), int(0.9 * self.property_width)),
                    Image.Resampling.LANCZOS,
                )
            )
        )

        self.red_token_image = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open(ASSET + "/red.png").resize(
                    (self.token_width, self.token_width),
                    Image.Resampling.LANCZOS,
                )
            )
        )
        self.green_token_image = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open(ASSET + "/green.png").resize(
                    (self.token_width, self.token_width),
                    Image.Resampling.LANCZOS,
                )
            )
        )
        self.blue_token_image = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open(ASSET + "/blue.png").resize(
                    (self.token_width, self.token_width),
                    Image.Resampling.LANCZOS,
                )
            )
        )
        self.yellow_token_image = ImageTk.PhotoImage(
            ImageOps.expand(
                Image.open(ASSET + "/yellow.png").resize(
                    (self.token_width, self.token_width),
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

        self.green_token = tk.Button(
            self.board_canvas,
            image=self.green_token_image,
            border=0,
            highlightthickness=0,
            command=lambda: self.player_frame_popup("Player 2"),
        )

        self.blue_token = tk.Button(
            self.board_canvas,
            image=self.blue_token_image,
            border=0,
            highlightthickness=0,
            command=lambda: self.player_frame_popup("Player 3"),
        )

        self.yellow_token = tk.Button(
            self.board_canvas,
            image=self.yellow_token_image,
            border=0,
            highlightthickness=0,
            command=lambda: self.player_frame_popup("Player 4"),
        )

        for i in self.player_details:
            self.move(i, 0)

    def hotel_rules(self):
        messagebox.showinfo("HOTEL RULES", "HOTEL RULES")

    def station_rules(self):
        messagebox.showinfo("STATION RULES", "STATION RULES")

    def utility_rules(self):
        messagebox.showinfo("UTILITY RULES", "UTILITY RULES")

    def jail_rules(self):
        messagebox.showinfo("JAIL RULES", "JAIL RULES")

    def count_colour(self, propertypos):
        owner = self.properties[propertypos].owner
        if owner:
            colour = self.properties[propertypos].colour
            c = 0
            for i in self.player_details[owner]["Properties"]:
                if i.colour == colour:
                    c += 1
            return c
        else:
            return None

    def owner_colour(self, propertypos):
        return self.player_details[self.properties[propertypos].owner]["Colour"]

    def owner_name(self, propertypos):
        return self.player_details[self.properties[propertypos].owner]["Name"]

    def buy_property(self, buyer, property):
        if not self.properties[property].owner:
            self.properties[property].owner = buyer
            l = self.player_details[buyer]["Properties"]
            l.append(self.properties[property])
            self.player_details[buyer].update({"Properties": l})

            if self.properties[property].colour in ["Brown", "Dark Blue"]:
                colour_set = 2
            else:
                colour_set = 3

            if self.count_colour(property) == colour_set:
                for i in self.properties.values():
                    if i.colour == self.properties[property].colour:
                        i.houses = 0
        else:
            print("Owned")

    def update_property_frame(self):
        if self.property_frame:
            self.delete_property_frame()
            self.property_frame_popup(self.property_pos_displayed)

    def station_property_frame(self, position):
        station_label = tk.Label(
            self.property_frame,
            image=self.station_image,
            border=0,
            highlightthickness=0,
        )
        station_label.place(relx=0.5, rely=0.2, anchor="center")

        tk.Label(
            self.property_frame,
            text=self.properties[position].name.upper(),
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
            height=(self.board_side - 2) // 3.2,
            bg="#F9FBFF",
        )
        canvas.place(relx=0.5, rely=0.7, anchor="center")
        canvas.update()
        y_coord = canvas.winfo_height() / 12

        ttk.Separator(canvas, orient="horizontal").place(
            relx=0.5, rely=0.85, anchor="center", relwidth=0.8
        )
        ttk.Separator(canvas, orient="horizontal").place(
            relx=0.5, rely=0.15, anchor="center", relwidth=0.8
        )

        tk.Button(
            self.property_frame,
            image=self.info_tag,
            border=0,
            highlightthickness=0,
            command=self.station_rules,
        ).place(x=35, rely=0.925, anchor="center")

        row_counter = 0
        stations_data = {
            "Unowned; Buy For": self.properties[position].price,
            "Rent": 25,
            "If 2 Stations are owned": 50,
            "If 3 Stations are owned": 100,
            "If 4 Stations are owned": 200,
        }
        for (
            i,
            j,
        ) in stations_data.items():  # Placing and formatting Rent data on card
            row_counter += 1
            try:
                if row_counter == self.count_colour(position) + 1:
                    canvas.create_text(
                        2,
                        y_coord - 2,
                        anchor="w",
                        text="▶",
                        font=("times", (self.board_side - 2) // 32),
                        fill=self.owner_colour(position),
                    )
            except:
                pass
            if row_counter == 1:
                if self.properties[position].owner:
                    canvas.create_text(
                        canvas.winfo_width() / 2,
                        y_coord,
                        anchor="center",
                        text=f"Owner: {self.owner_name(position)}",
                        font=("times", (self.board_side - 2) // 45),
                        fill=self.owner_colour(position),
                    )
                else:
                    canvas.create_text(
                        2,
                        y_coord - 2,
                        anchor="w",
                        text="▶",
                        font=("times", (self.board_side - 2) // 32),
                    )
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

            y_coord += canvas.winfo_height() / 6
        canvas.create_text(
            45,
            y_coord,
            anchor="w",
            text="Mortgage Value",
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
            text=self.properties[position].mortgage,
            font=("times", (self.board_side - 2) // 51),
        )

    def utility_property_frame(self, position):
        if position == 28:
            utility_image = self.water_image
        else:
            utility_image = self.electric_image
        utility_label = tk.Label(
            self.property_frame, image=utility_image, border=0, highlightthickness=0
        )
        utility_label.place(relx=0.5, rely=0.2, anchor="center")

        tk.Label(
            self.property_frame,
            text=self.properties[position].name.upper(),
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
            height=(self.board_side - 2) // 3.2,
            bg="#F9FBFF",
        )
        canvas.place(relx=0.5, rely=0.7, anchor="center")
        canvas.update()
        y_coord = canvas.winfo_height() / 14

        ttk.Separator(canvas, orient="horizontal").place(
            relx=0.5, rely=0.85, anchor="center", relwidth=0.8
        )

        ttk.Separator(canvas, orient="horizontal").place(
            relx=0.5, rely=0.15, anchor="center", relwidth=0.8
        )

        tk.Button(
            self.property_frame,
            image=self.info_tag,
            border=0,
            highlightthickness=0,
            command=self.utility_rules,
        ).place(x=35, rely=0.925, anchor="center")

        row_counter = 0
        try:  # if dice has been rolled
            utilities_data = {
                "Unowned; Buy For": self.properties[position].price,
                f"Rent based on last roll ({self.current_move}),": None,
                "If 1 utility is owned:": None,
                f" 4   x  {self.current_move}     = ": 4 * self.current_move,
                "If 2 utilities are owned:": None,
                f"10  x  {self.current_move}     =": 10 * self.current_move,
            }
        except:  # if dice has not been rolled yet
            utilities_data = {
                "Unowned; Buy For": self.properties[position].price,
                "Rent based on roll (10),": None,
                "If 1 utility is owned:": None,
                f" 4   x  10     = ": 40,
                "If 2 utilities are owned:": None,
                f"10  x  10     =": 100,
            }
        for (
            i,
            j,
        ) in utilities_data.items():  # Placing and formatting Rent data on card
            row_counter += 1
            try:
                if row_counter == self.count_colour(position) * 2 + 1:
                    canvas.create_text(
                        2,
                        y_coord - 2,
                        anchor="w",
                        text="▶",
                        font=("times", (self.board_side - 2) // 32),
                        fill=self.owner_colour(position),
                    )
            except:
                pass
            if row_counter == 1:
                if self.properties[position].owner:
                    canvas.create_text(
                        canvas.winfo_width() / 2,
                        y_coord,
                        anchor="center",
                        text=f"Owner: {self.owner_name(position)}",
                        font=("times", (self.board_side - 2) // 45),
                        fill=self.owner_colour(position),
                    )
                else:
                    canvas.create_text(
                        2,
                        y_coord - 2,
                        anchor="w",
                        text="▶",
                        font=("times", (self.board_side - 2) // 32),
                    )
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
            elif row_counter in [2, 3, 5]:  # text row
                canvas.create_text(
                    25,
                    y_coord,
                    anchor="w",
                    text=i,
                    font=("times", (self.board_side - 2) // 45),
                )
            elif row_counter in [4, 6]:  # rent row
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

            y_coord += canvas.winfo_height() / 7
        canvas.create_text(
            45,
            y_coord,
            anchor="w",
            text="Mortgage Value",
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
            text=self.properties[position].mortgage,
            font=("times", (self.board_side - 2) // 51),
        )

    def title_deed_popup(self, position):
        title_frame = tk.Frame(
            self.property_frame,
            width=(self.board_side - 2) // 2.25,
            height=(self.board_side - 2) // 10,
            bg=self.properties[position].hex,
            highlightthickness=2,
            highlightbackground="black",
        )
        title_frame.place(relx=0.5, rely=0.125, anchor="center")

        tk.Label(
            title_frame,
            text="TITLE DEED",
            font=("times", (self.board_side - 2) // 56),
            bg=self.properties[position].hex,
        ).place(relx=0.5, rely=0.25, anchor="center")

        tk.Label(
            title_frame,
            text=self.properties[position].name.upper(),
            font=("times", (self.board_side - 2) // 42),
            bg=self.properties[position].hex,
        ).place(relx=0.5, rely=0.65, anchor="center")

        tk.Button(
            title_frame,
            text="✕",
            font=("courier", (self.board_side - 2) // 60),
            bg=self.properties[position].hex,
            highlightthickness=0,
            border=0,
            activebackground=self.properties[position].hex,
            command=self.delete_property_frame,
        ).place(relx=1, rely=0, anchor="ne")

        canvas = tk.Canvas(
            self.property_frame,
            highlightthickness=0,
            width=(self.board_side - 2) // 2.25,
            height=(self.board_side - 2) // 2.3,
            bg="#F9FBFF",
        )
        canvas.place(relx=0.5, rely=0.6, anchor="center")
        canvas.update()
        y_coord = canvas.winfo_height() / 23

        ttk.Separator(canvas, orient="horizontal").place(
            relx=0.5, rely=0.725, anchor="center", relwidth=0.8
        )

        ttk.Separator(canvas, orient="horizontal").place(
            relx=0.5, rely=0.09, anchor="center", relwidth=0.8
        )

        tk.Button(
            self.property_frame,
            image=self.info_tag,
            border=0,
            highlightthickness=0,
            command=self.hotel_rules,
        ).place(x=35, rely=0.9, anchor="center")

        vals = [self.properties[position].price]
        vals.extend(self.properties[position].rent_values)
        vals.extend(
            [
                self.properties[position].mortgage,
                self.properties[position].build,
                self.properties[position].build,
            ]
        )
        d = dict(
            zip(
                [
                    "Unowned; Buy For",
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
                vals,
            )
        )

        row_counter = -3
        for i, j in d.items():  # Placing and formatting Rent data on card
            row_counter += 1
            try:
                if row_counter == self.properties[position].houses:
                    canvas.create_text(
                        2,
                        y_coord - 2,
                        anchor="w",
                        text="▶",
                        font=("times", (self.board_side - 2) // 32),
                        fill=self.owner_colour(position),
                    )
            except:
                pass

            if row_counter == -2:
                if self.properties[position].owner:
                    canvas.create_text(
                        canvas.winfo_width() / 2,
                        y_coord,
                        anchor="center",
                        text=f"Owner: {self.owner_name(position)}",
                        font=("times", (self.board_side - 2) // 45),
                        fill=self.owner_colour(position),
                    )
                else:
                    canvas.create_text(
                        2,
                        y_coord - 2,
                        anchor="w",
                        text="▶",
                        font=("times", (self.board_side - 2) // 32),
                    )
                    canvas.create_text(
                        25,
                        y_coord,
                        anchor="w",
                        text=i,
                        font=("times", (self.board_side - 2) // 45),
                    )
                    canvas.create_text(
                        canvas.winfo_width() / 1.375,
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

            y_coord += canvas.winfo_height() / 11

    def property_frame_popup(self, position):
        if self.property_frame:
            self.delete_property_frame()
        self.property_pos_displayed = position
        self.property_frame = tk.Frame(
            self.main_frame,
            width=(self.board_side - 2) // 2.05,
            height=(self.board_side - 2) // 1.75,
            bg="#F9FBFF",
            highlightthickness=2,
            highlightbackground="black",
        )

        self.property_frame.place(relx=1, rely=1, anchor="se")

        if position in [5, 15, 25, 35]:
            self.station_property_frame(position)
        elif position in [12, 28]:
            self.utility_property_frame(position)
        else:
            self.title_deed_popup(position)

    def delete_property_frame(self):
        self.property_frame.place_forget()
        self.property_frame = None
        self.property_pos_displayed = None

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

    def roll_dice(self):  # TODO: Doubles Roll Again --- Disabling buttons
        if self.me % len(self.player_details):
            player = self.me % len(self.player_details)
        else:
            player = len(self.player_details)
        mixer.music.load(ASSET + "/diceroll.mp3")
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
        self.dice_spot1.update()
        self.dice_spot2.update()
        self.current_move = sum(dice_roll)
        self.move(player, self.current_move)
        self.me += 1  # updating me to iterate through all for now

    def click_to_position(self, event):
        x, y = event.x, event.y
        l = [1.6, 1.6]
        l[1:1] = [1] * 9
        pos = 0
        if x <= self.property_height:
            for i in range(len(l)):
                if y > sum(l[i + 1 :]) / sum(l) * self.board_side:
                    pos = 10 + i
                    break
        elif x >= self.board_side - self.property_height:
            for i in range(len(l)):
                if y > sum(l[i + 1 :]) / sum(l) * self.board_side:
                    pos = (40 - i) % 40
                    break
        elif y <= self.property_height:
            for i in range(len(l)):
                if x > sum(l[i + 1 :]) / sum(l) * self.board_side:
                    pos = 30 - i
                    break
        elif y >= self.board_side - self.property_height:
            for i in range(len(l)):
                if x > sum(l[i + 1 :]) / sum(l) * self.board_side:
                    pos = i
                    break
        if self.properties[pos].colour:
            self.property_frame_popup(pos)
        else:
            pass

    def position_to_xy(
        self, position
    ):  # +1, +2, because canvas has random error and places image 2,2 up and left, so image is placed at 2,2 and not 0,0
        l = [1.6, 1.6]
        l[1:1] = [1] * 9
        position %= 40
        if position == 0:
            x1 = self.board_side + 1
            y1 = self.board_side - self.property_height + 2
        elif position <= 10:
            x1 = sum(l[:-(position)]) * self.property_width + 1
            y1 = self.board_side - self.property_height + 2
        elif position <= 20:
            x1 = self.property_height + 2
            y1 = sum(l[: -(position - 9)]) * self.property_width + 1
        elif position <= 30:
            x1 = sum(l[: (position - 19)]) * self.property_width + 1
            y1 = 0 + 2
        elif position < 40:
            x1 = self.board_side + 2
            y1 = sum(l[: (position - 30)]) * self.property_width + 1
        # self.board_canvas.create_rectangle(x1,y1,x1-self.property_height,y1+self.property_height,outline='blue',width=3)
        return x1, y1

    def position_to_tokenxy(self, player, position):
        position %= 40

        x1, y1 = self.position_to_xy(position)
        if position == 10:
            if self.player_details[player]["Injail"]:
                x = x1 - (self.property_height * 0.35)
                y = y1 + (self.property_height * 0.35)
            else:
                if self.player_details[player]["Colour"] == "red":
                    return int(
                        self.token_width / 2 + self.property_height * 0.075
                    ), int(y1 + self.property_height * 0.3 - self.token_width / 2)
                elif self.player_details[player]["Colour"] == "green":
                    return int(
                        self.token_width / 2 + self.property_height * 0.075
                    ), int(y1 + self.property_height * 0.6 - self.token_width / 2)
                elif self.player_details[player]["Colour"] == "blue":
                    return int(
                        x1 - self.property_height * 0.6 + self.token_width / 2 + 3
                    ), int(y1 + self.property_height * 0.95 - self.token_width / 2)
                elif self.player_details[player]["Colour"] == "gold":
                    return int(
                        x1 - self.property_height * 0.3 + self.token_width / 2 + 3
                    ), int(y1 + self.property_height * 0.95 - self.token_width / 2)
        elif not position % 10:
            x = x1 - (self.property_height * 0.5)
            y = y1 + (self.property_height * 0.5)
        elif position < 10:
            x = x1 - (self.property_width * 0.5)
            y = y1 + (self.property_height * 0.6)
        elif position < 20:
            x = x1 - (self.property_height * 0.6)
            y = y1 + (self.property_width * 0.5)
        elif position < 30:
            x = x1 - (self.property_width * 0.5)
            y = y1 + (self.property_height * 0.4)
        elif position < 40:
            x = x1 - (self.property_height * 0.4)
            y = y1 + (self.property_width * 0.5)

        if self.player_details[player]["Colour"] == "red":
            return int(x - self.token_width / 2 - 1), int(y - self.token_width / 2)
        elif self.player_details[player]["Colour"] == "green":
            return int(x + self.token_width / 2 + 1), int(y - self.token_width / 2)
        elif self.player_details[player]["Colour"] == "blue":
            return int(x - self.token_width / 2 - 1), int(y + self.token_width / 2 + 2)
        elif self.player_details[player]["Colour"] == "gold":
            return int(x + self.token_width / 2 + 1), int(y + self.token_width / 2 + 2)

    def move(self, player, move):
        colour = self.player_details[player]["Colour"]
        self.colour_token_dict = {
            "red": self.red_token,
            "green": self.green_token,
            "blue": self.blue_token,
            "gold": self.yellow_token,
        }

        if move:
            for i in range(move):
                self.player_details[player]["Position"] += 1
                x1, y1 = self.position_to_tokenxy(
                    player, self.player_details[player]["Position"]
                )
                self.colour_token_dict[colour].place(x=x1, y=y1, anchor="center")
                sleep(0.2)
                self.colour_token_dict[colour].update()
        else:
            x1, y1 = self.position_to_tokenxy(
                player, self.player_details[player]["Position"]
            )
            self.colour_token_dict[colour].place(x=x1, y=y1, anchor="center")


# TODO: Make popups for other locations (INFO, Rules)

# scroll = ttk.Scrollbar(dataframe,orient=tk.VERTICAL)
# scroll.place(relx=1,rely=0,anchor='ne',relheight=1)
# scroll.config(command=listbox.yview)

root = tk.Tk()
mono = Monopoly(
    {
        1: {"Name": "Player 1", "Colour": "red"},
        2: {"Name": "Player 2", "Colour": "green"},
        3: {"Name": "Player 3", "Colour": "blue"},
        4: {"Name": "Player 4", "Colour": "gold"},
    },
    1,
)


def CLI():
    while True:
        t = tuple(int(i) for i in input().split())
        if t[0] == 13:
            try:
                mono.move(t[1], t[2])
            except:
                pass
        elif t[0] == 2:
            try:
                mono.buy_property(t[1], t[2])
            except:
                pass
        else:
            break


t = threading.Thread(target=CLI)
t.start()

update_property = threading.Thread(target=mono.update_property_frame)
update_property.start()  # TODO: Fix thread

mono.start_monopoly()
root.mainloop()
