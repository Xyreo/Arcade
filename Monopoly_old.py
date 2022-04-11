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

root = tk.Tk()  # Start Window
mixer.init()  # pygame music player initialise

# region #main game window
monopoly_window = tk.Toplevel()
monopoly_window.title("Monopoly")
monopoly_window.resizable(False, False)
monopoly_window.config(bg="white")
monopoly_window.protocol("WM_DELETE_WINDOW", root.destroy)

screen_width = int(0.9 * monopoly_window.winfo_screenwidth())
screen_height = int(screen_width / 1.9)
x_coord = monopoly_window.winfo_screenwidth() // 2 - screen_width // 2
y_coord = (monopoly_window.winfo_screenheight() - 70) // 2 - screen_height // 2

monopoly_window.geometry(f"{screen_width}x{screen_height}+{x_coord}+{y_coord}")

# Withdrawing Monopoly screen initially, to show only when game starts
monopoly_window.withdraw()

board_side = screen_height - 65  # Length of board
property_width = board_side / 12.2  # Width of one property on board

board_canvas = tk.Canvas(monopoly_window, width=board_side, height=board_side)
board_canvas.place(relx=0.01, rely=0.04, anchor="nw")

main_frame = tk.Frame(
    monopoly_window, width=board_side - 2, height=board_side - 2, background="white"
)
main_frame.place(relx=0.99, rely=0.04, anchor="ne")
# endregion


def start_monopoly():  # Starting Game, withdrawing start window
    global monopoly_window
    monopoly_window.deiconify()
    root.withdraw()


# temp start button
start = ttk.Button(root, text="START", command=start_monopoly).pack()

# region #Image Objects
board_image = ImageTk.PhotoImage(
    ImageOps.expand(
        Image.open("Assets/BoardIMG.jpg").resize(
            (board_side, board_side), Image.ANTIALIAS
        )
    )
)

board_canvas.create_image(2, 2, image=board_image, anchor="nw")
# board_label = tk.Label(board_frame, image=board_image).place(
#     relx=0.499, rely=0.499, anchor="center"
# )

small_info_tag = ImageTk.PhotoImage(
    ImageOps.expand(
        Image.open("Assets/small_info.png").resize(
            (int(property_width / 5.5), int(property_width / 5.5)), Image.ANTIALIAS
        )
    )
)

big_info_tag = ImageTk.PhotoImage(
    ImageOps.expand(
        Image.open("Assets/big_info.png").resize(
            (int(property_width / 2), int(property_width / 2)), Image.ANTIALIAS
        )
    )
)

station_image = ImageTk.PhotoImage(
    ImageOps.expand(
        Image.open("Assets/station.png").resize(
            (int(2.5 * property_width), int(2.5 * property_width)), Image.ANTIALIAS
        )
    )
)

water_image = ImageTk.PhotoImage(
    ImageOps.expand(
        Image.open("Assets/water.png").resize(
            (int(2.5 * property_width), int(2 * property_width)), Image.ANTIALIAS
        )
    )
)

electric_image = ImageTk.PhotoImage(
    ImageOps.expand(
        Image.open("Assets/electric.png").resize(
            (int(2 * property_width), int(2.25 * property_width)), Image.ANTIALIAS
        )
    )
)

dice1 = ImageTk.PhotoImage(
    ImageOps.expand(
        Image.open("Assets/dice1.png").resize(
            (int(0.9 * property_width), int(0.9 * property_width)), Image.ANTIALIAS
        )
    )
)
dice2 = ImageTk.PhotoImage(
    ImageOps.expand(
        Image.open("Assets/dice2.png").resize(
            (int(0.9 * property_width), int(0.9 * property_width)), Image.ANTIALIAS
        )
    )
)
dice3 = ImageTk.PhotoImage(
    ImageOps.expand(
        Image.open("Assets/dice3.png").resize(
            (int(0.9 * property_width), int(0.9 * property_width)), Image.ANTIALIAS
        )
    )
)
dice4 = ImageTk.PhotoImage(
    ImageOps.expand(
        Image.open("Assets/dice4.png").resize(
            (int(0.9 * property_width), int(0.9 * property_width)), Image.ANTIALIAS
        )
    )
)
dice5 = ImageTk.PhotoImage(
    ImageOps.expand(
        Image.open("Assets/dice5.png").resize(
            (int(0.9 * property_width), int(0.9 * property_width)), Image.ANTIALIAS
        )
    )
)
dice6 = ImageTk.PhotoImage(
    ImageOps.expand(
        Image.open("Assets/dice6.png").resize(
            (int(0.9 * property_width), int(0.9 * property_width)), Image.ANTIALIAS
        )
    )
)

red_token_image = ImageTk.PhotoImage(
    ImageOps.expand(
        Image.open("Assets/red.png").resize(
            (board_side // 39, board_side // 39), Image.ANTIALIAS
        )
    )
)
green_token_image = ImageTk.PhotoImage(
    ImageOps.expand(
        Image.open("Assets/green.png").resize(
            (board_side // 39, board_side // 39), Image.ANTIALIAS
        )
    )
)
blue_token_image = ImageTk.PhotoImage(
    ImageOps.expand(
        Image.open("Assets/blue.png").resize(
            (board_side // 39, board_side // 39), Image.ANTIALIAS
        )
    )
)
yellow_token_image = ImageTk.PhotoImage(
    ImageOps.expand(
        Image.open("Assets/yellow.png").resize(
            (board_side // 39, board_side // 39), Image.ANTIALIAS
        )
    )
)
# endregion

# region #info tags on board
posvar = board_side - property_width / 5.5

tk.Button(
    board_canvas,
    image=small_info_tag,
    border=0,
    highlightthickness=0,
    command=lambda: property_frame_popup("Old Kent Road"),
).place(x=posvar - 1.6 * property_width, y=posvar, anchor="center")

tk.Button(
    board_canvas,
    image=small_info_tag,
    border=0,
    highlightthickness=0,
    command=lambda: property_frame_popup("Whitechapel Road"),
).place(x=posvar - 3.6 * property_width, y=posvar, anchor="center")

tk.Button(
    board_canvas,
    image=small_info_tag,
    border=0,
    highlightthickness=0,
    command=lambda: property_frame_popup("Kings Cross Station"),
).place(x=posvar - 5.6 * property_width, y=posvar, anchor="center")

tk.Button(
    board_canvas,
    image=small_info_tag,
    border=0,
    highlightthickness=0,
    command=lambda: property_frame_popup("The Angel, Islington"),
).place(x=posvar - 6.6 * property_width, y=posvar, anchor="center")

tk.Button(
    board_canvas,
    image=small_info_tag,
    border=0,
    highlightthickness=0,
    command=lambda: property_frame_popup("Euston Road"),
).place(x=posvar - 8.6 * property_width, y=posvar, anchor="center")

tk.Button(
    board_canvas,
    image=small_info_tag,
    border=0,
    highlightthickness=0,
    command=lambda: property_frame_popup("Pentonville Road"),
).place(x=posvar - 9.6 * property_width, y=posvar, anchor="center")

tk.Button(
    board_canvas,
    image=small_info_tag,
    border=0,
    highlightthickness=0,
    command=lambda: jail_rules(),
).place(x=posvar - 11.8 * property_width, y=posvar, anchor="center")

tk.Button(
    board_canvas,
    image=small_info_tag,
    border=0,
    highlightthickness=0,
    command=lambda: property_frame_popup("Pall Mall"),
).place(
    x=posvar - 11.825 * property_width, y=posvar - 1.6 * property_width, anchor="center"
)

tk.Button(
    board_canvas,
    image=small_info_tag,
    border=0,
    highlightthickness=0,
    command=lambda: property_frame_popup("Electric Company"),
).place(
    x=posvar - 11.825 * property_width, y=posvar - 2.6 * property_width, anchor="center"
)

tk.Button(
    board_canvas,
    image=small_info_tag,
    border=0,
    highlightthickness=0,
    command=lambda: property_frame_popup("Whitehall"),
).place(
    x=posvar - 11.825 * property_width, y=posvar - 3.6 * property_width, anchor="center"
)

tk.Button(
    board_canvas,
    image=small_info_tag,
    border=0,
    highlightthickness=0,
    command=lambda: property_frame_popup("Northumbl'd Avenue"),
).place(
    x=posvar - 11.825 * property_width, y=posvar - 4.6 * property_width, anchor="center"
)

tk.Button(
    board_canvas,
    image=small_info_tag,
    border=0,
    highlightthickness=0,
    command=lambda: property_frame_popup("Marylebone Station"),
).place(
    x=posvar - 11.825 * property_width, y=posvar - 5.6 * property_width, anchor="center"
)

tk.Button(
    board_canvas,
    image=small_info_tag,
    border=0,
    highlightthickness=0,
    command=lambda: property_frame_popup("Bow Street"),
).place(
    x=posvar - 11.825 * property_width, y=posvar - 6.6 * property_width, anchor="center"
)

tk.Button(
    board_canvas,
    image=small_info_tag,
    border=0,
    highlightthickness=0,
    command=lambda: property_frame_popup("Marlborough Street"),
).place(
    x=posvar - 11.825 * property_width, y=posvar - 8.6 * property_width, anchor="center"
)

tk.Button(
    board_canvas,
    image=small_info_tag,
    border=0,
    highlightthickness=0,
    command=lambda: property_frame_popup("Vine Street"),
).place(
    x=posvar - 11.825 * property_width, y=posvar - 9.6 * property_width, anchor="center"
)

tk.Button(
    board_canvas,
    image=small_info_tag,
    border=0,
    highlightthickness=0,
    command=lambda: property_frame_popup("Strand"),
).place(
    x=posvar - 10.21 * property_width,
    y=posvar - 11.825 * property_width,
    anchor="center",
)

tk.Button(
    board_canvas,
    image=small_info_tag,
    border=0,
    highlightthickness=0,
    command=lambda: property_frame_popup("Fleet Street"),
).place(
    x=posvar - 8.21 * property_width,
    y=posvar - 11.825 * property_width,
    anchor="center",
)

tk.Button(
    board_canvas,
    image=small_info_tag,
    border=0,
    highlightthickness=0,
    command=lambda: property_frame_popup("Trafalgar Square"),
).place(
    x=posvar - 7.21 * property_width,
    y=posvar - 11.825 * property_width,
    anchor="center",
)

tk.Button(
    board_canvas,
    image=small_info_tag,
    border=0,
    highlightthickness=0,
    command=lambda: property_frame_popup("Fenchurch St. Station"),
).place(
    x=posvar - 6.21 * property_width,
    y=posvar - 11.825 * property_width,
    anchor="center",
)

tk.Button(
    board_canvas,
    image=small_info_tag,
    border=0,
    highlightthickness=0,
    command=lambda: property_frame_popup("Leicester Square"),
).place(
    x=posvar - 5.21 * property_width,
    y=posvar - 11.825 * property_width,
    anchor="center",
)

tk.Button(
    board_canvas,
    image=small_info_tag,
    border=0,
    highlightthickness=0,
    command=lambda: property_frame_popup("Coventry Street"),
).place(
    x=posvar - 4.21 * property_width,
    y=posvar - 11.825 * property_width,
    anchor="center",
)

tk.Button(
    board_canvas,
    image=small_info_tag,
    border=0,
    highlightthickness=0,
    command=lambda: property_frame_popup("Water Works"),
).place(
    x=posvar - 3.21 * property_width,
    y=posvar - 11.825 * property_width,
    anchor="center",
)

tk.Button(
    board_canvas,
    image=small_info_tag,
    border=0,
    highlightthickness=0,
    command=lambda: property_frame_popup("Piccadilly"),
).place(
    x=posvar - 2.21 * property_width,
    y=posvar - 11.825 * property_width,
    anchor="center",
)

tk.Button(
    board_canvas,
    image=small_info_tag,
    border=0,
    highlightthickness=0,
    command=lambda: jail_rules(),
).place(x=posvar, y=posvar - 11.825 * property_width, anchor="center")

tk.Button(
    board_canvas,
    image=small_info_tag,
    border=0,
    highlightthickness=0,
    command=lambda: property_frame_popup("Regent Street"),
).place(x=posvar, y=posvar - 10.2 * property_width, anchor="center")

tk.Button(
    board_canvas,
    image=small_info_tag,
    border=0,
    highlightthickness=0,
    command=lambda: property_frame_popup("Oxford Street"),
).place(x=posvar, y=posvar - 9.2 * property_width, anchor="center")

tk.Button(
    board_canvas,
    image=small_info_tag,
    border=0,
    highlightthickness=0,
    command=lambda: property_frame_popup("Bond Street"),
).place(x=posvar, y=posvar - 7.2 * property_width, anchor="center")

tk.Button(
    board_canvas,
    image=small_info_tag,
    border=0,
    highlightthickness=0,
    command=lambda: property_frame_popup("Liverpool St. Station"),
).place(x=posvar, y=posvar - 6.2 * property_width, anchor="center")

tk.Button(
    board_canvas,
    image=small_info_tag,
    border=0,
    highlightthickness=0,
    command=lambda: property_frame_popup("Park Lane"),
).place(x=posvar, y=posvar - 4.2 * property_width, anchor="center")

tk.Button(
    board_canvas,
    image=small_info_tag,
    border=0,
    highlightthickness=0,
    command=lambda: property_frame_popup("Mayfair"),
).place(x=posvar, y=posvar - 2.2 * property_width, anchor="center")
# endregion

# region #Dice and tokens
die_dict = dict(zip((1, 2, 3, 4, 5, 6), (dice1, dice2, dice3, dice4, dice5, dice6)))

red_token = tk.Button(
    board_canvas,
    image=red_token_image,
    border=0,
    highlightthickness=0,
    command=lambda: player_frame_popup("Player 1"),
)
red_token.place(
    x=board_side - 1.2 * property_width,
    y=board_side - 0.75 * property_width,
    anchor="center",
)

green_token = tk.Button(
    board_canvas,
    image=green_token_image,
    border=0,
    highlightthickness=0,
    command=lambda: player_frame_popup("Player 2"),
)
green_token.place(
    x=board_side - 0.85 * property_width,
    y=board_side - 0.75 * property_width,
    anchor="center",
)

blue_token = tk.Button(
    board_canvas,
    image=blue_token_image,
    border=0,
    highlightthickness=0,
    command=lambda: player_frame_popup("Player 3"),
)
blue_token.place(
    x=board_side - 1.2 * property_width,
    y=board_side - 0.4 * property_width,
    anchor="center",
)

yellow_token = tk.Button(
    board_canvas,
    image=yellow_token_image,
    border=0,
    highlightthickness=0,
    command=lambda: player_frame_popup("Player 4"),
)
yellow_token.place(
    x=board_side - 0.85 * property_width,
    y=board_side - 0.4 * property_width,
    anchor="center",
)

button_style = ttk.Style()
button_style.configure("my.TButton", font=("times", int(property_width / 3)))

roll_button = ttk.Button(
    board_canvas, text="Roll Dice", style="my.TButton", command=lambda: roll_dice()
)
roll_button.place(relx=0.5, rely=0.5, anchor="center")

dice_spot1 = tk.Label(board_canvas, image=dice5, border=0, highlightthickness=0)
dice_spot1.place(relx=0.485, rely=0.46, anchor="se")

dice_spot2 = tk.Label(board_canvas, image=dice5, border=0, highlightthickness=0)
dice_spot2.place(relx=0.515, rely=0.46, anchor="sw")
# endregion

# region #DATABASE STUFF, temporary random variables for now
d = {}
d["Mayfair"] = dict(
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
property_color = "#016cbf"
player_color = "red"
owner = "Player 1"
houses = 0  # [-1 to 5]

owner_stations_owned = 2
owner_utilities_owned = 1

dictionary = {
    0: ["player1", red_token, 0],
    1: ["player2", green_token, 0],
    2: ["player3", blue_token, 0],
    3: ["player4", yellow_token, 0],
}
check, player = 0, []
injail = False

# 'check' variable for moving token turn by turn for now because checking

# endregion


def hotel_rules():
    messagebox.showinfo("HOTEL RULES", "HOTEL RULES")


def station_rules():
    messagebox.showinfo("STATION RULES", "STATION RULES")


def utility_rules():
    messagebox.showinfo("UTILITY RULES", "UTILITY RULES")


def jail_rules():
    messagebox.showinfo("JAIL RULES", "JAIL RULES")


# TODO: Make Thread to update all frames, based on game progress
def property_frame_popup(property):
    global property_frame
    if property_frame:
        delete_property_frame()
    property_frame = tk.Frame(
        main_frame,
        width=(board_side - 2) // 2.05,
        height=(board_side - 2) // 1.75,
        bg="#F9FBFF",
        highlightthickness=2,
        highlightbackground="black",
    )

    property_frame.place(relx=1, rely=1, anchor="se")

    if "station" in property.lower():
        station_label = tk.Label(
            property_frame, image=station_image, border=0, highlightthickness=0
        )
        station_label.place(relx=0.5, rely=0.2, anchor="center")

        tk.Label(
            property_frame,
            text=property.upper(),
            font=("times", (board_side - 2) // 40),
            bg="#F9FBFF",
        ).place(relx=0.5, rely=0.4, anchor="center")

        tk.Button(
            property_frame,
            text="✕",
            font=("courier", (board_side - 2) // 60),
            bg="#F9FBFF",
            highlightthickness=0,
            border=0,
            activebackground="#F9FBFF",
            command=delete_property_frame,
        ).place(relx=0.95, rely=0.05, anchor="ne")

        canvas = tk.Canvas(
            property_frame,
            highlightthickness=0,
            width=(board_side - 2) // 2.25,
            height=(board_side - 2) // 4,
            bg="#F9FBFF",
        )
        canvas.place(relx=0.5, rely=0.725, anchor="center")
        canvas.update()
        y_coord = canvas.winfo_height() / 10

        ttk.Separator(canvas, orient="horizontal").place(
            relx=0.5, rely=0.8, anchor="center", relwidth=0.8
        )

        tk.Label(
            property_frame,
            text=f"Owner: {owner}",
            font=("times", (board_side - 2) // 46),
            fg=player_color,
            bg="#F9FBFF",
        ).place(relx=0.5, rely=0.475, anchor="center")

        tk.Button(
            property_frame,
            image=big_info_tag,
            border=0,
            highlightthickness=0,
            command=station_rules,
        ).place(x=35, rely=0.9, anchor="center")

        row_counter = 0
        stations_data = {
            "Rent": 25,
            "If 2 Stations are owned": 50,
            "If 3 Stations are owned": 100,
            "If 4 Stations are owned": 200,
            "Mortgage Value": 100,
        }
        for i, j in stations_data.items():  # Placing and formatting Rent data on card
            row_counter += 1
            if row_counter == owner_stations_owned:
                canvas.create_text(
                    2,
                    y_coord - 2,
                    anchor="w",
                    text="▶",
                    font=("times", (board_side - 2) // 32),
                    fill=player_color,
                )
            if row_counter == 5:  # mortgage
                canvas.create_text(
                    45,
                    y_coord,
                    anchor="w",
                    text=i,
                    font=("times", (board_side - 2) // 51),
                )
                canvas.create_text(
                    canvas.winfo_width() / 1.3,
                    y_coord,
                    text="₩",
                    angle=180,
                    font=("courier", (board_side - 2) // 51),
                )
                canvas.create_text(
                    canvas.winfo_width() - 35,
                    y_coord,
                    anchor="e",
                    text=str(j),
                    font=("times", (board_side - 2) // 51),
                )
            else:
                canvas.create_text(
                    25,
                    y_coord,
                    anchor="w",
                    text=i,
                    font=("times", (board_side - 2) // 45),
                )
                canvas.create_text(
                    canvas.winfo_width() / 1.3,
                    y_coord,
                    text="₩",
                    angle=180,
                    font=("courier", (board_side - 2) // 45),
                )
                canvas.create_text(
                    canvas.winfo_width() - 25,
                    y_coord,
                    anchor="e",
                    text=str(j),
                    font=("times", (board_side - 2) // 45),
                )

            y_coord += canvas.winfo_height() / 5

    elif any([a in property.lower() for a in ["water", "electric"]]):
        if "water" in property.lower():
            utility_image = water_image
        else:
            utility_image = electric_image
        utility_label = tk.Label(
            property_frame, image=utility_image, border=0, highlightthickness=0
        )
        utility_label.place(relx=0.5, rely=0.2, anchor="center")

        tk.Label(
            property_frame,
            text=property.upper(),
            font=("times", (board_side - 2) // 40),
            bg="#F9FBFF",
        ).place(relx=0.5, rely=0.4, anchor="center")

        tk.Button(
            property_frame,
            text="✕",
            font=("courier", (board_side - 2) // 60),
            bg="#F9FBFF",
            highlightthickness=0,
            border=0,
            activebackground="#F9FBFF",
            command=delete_property_frame,
        ).place(relx=0.95, rely=0.05, anchor="ne")

        canvas = tk.Canvas(
            property_frame,
            highlightthickness=0,
            width=(board_side - 2) // 2.25,
            height=(board_side - 2) // 4,
            bg="#F9FBFF",
        )
        canvas.place(relx=0.5, rely=0.725, anchor="center")
        canvas.update()
        y_coord = canvas.winfo_height() / 12

        ttk.Separator(canvas, orient="horizontal").place(
            relx=0.5, rely=0.85, anchor="center", relwidth=0.8
        )

        tk.Label(
            property_frame,
            text=f"Owner: {owner}",
            font=("times", (board_side - 2) // 46),
            fg=player_color,
            bg="#F9FBFF",
        ).place(relx=0.5, rely=0.475, anchor="center")

        tk.Button(
            property_frame,
            image=big_info_tag,
            border=0,
            highlightthickness=0,
            command=utility_rules,
        ).place(x=35, rely=0.925, anchor="center")

        row_counter = 0
        try:  # if dice has been rolled
            utilities_data = {
                f"Rent based on last roll ({current_move}),": None,
                "If 1 utility is owned:": None,
                f" 4   x  {current_move}     = ": 4 * current_move,
                "If 2 utilities are owned:": None,
                f"10  x  {current_move}     =": 10 * current_move,
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
        for i, j in utilities_data.items():  # Placing and formatting Rent data on card
            row_counter += 1
            if row_counter == owner_utilities_owned * 2:
                canvas.create_text(
                    2,
                    y_coord - 2,
                    anchor="w",
                    text="▶",
                    font=("times", (board_side - 2) // 32),
                    fill=player_color,
                )
            if row_counter in [1, 2, 4]:  # text row
                canvas.create_text(
                    25,
                    y_coord,
                    anchor="w",
                    text=i,
                    font=("times", (board_side - 2) // 45),
                )
            elif row_counter in [3, 5]:  # rent row
                canvas.create_text(
                    canvas.winfo_width() / 2.75,
                    y_coord,
                    anchor="w",
                    text=i,
                    font=("times", (board_side - 2) // 45),
                )
                canvas.create_text(
                    canvas.winfo_width() / 1.3,
                    y_coord,
                    text="₩",
                    angle=180,
                    font=("courier", (board_side - 2) // 45),
                )
                canvas.create_text(
                    canvas.winfo_width() - 25,
                    y_coord,
                    anchor="e",
                    text=str(j),
                    font=("times", (board_side - 2) // 45),
                )
            elif row_counter == 6:  # mortgage
                canvas.create_text(
                    45,
                    y_coord * 1.025,
                    anchor="w",
                    text=i,
                    font=("times", (board_side - 2) // 51),
                )
                canvas.create_text(
                    canvas.winfo_width() / 1.3,
                    y_coord * 1.025,
                    text="₩",
                    angle=180,
                    font=("courier", (board_side - 2) // 51),
                )
                canvas.create_text(
                    canvas.winfo_width() - 35,
                    y_coord * 1.025,
                    anchor="e",
                    text=str(j),
                    font=("times", (board_side - 2) // 51),
                )

            y_coord += canvas.winfo_height() / 6

    else:
        title_frame = tk.Frame(
            property_frame,
            width=(board_side - 2) // 2.25,
            height=(board_side - 2) // 10,
            bg=property_color,
            highlightthickness=2,
            highlightbackground="black",
        )
        title_frame.place(relx=0.5, rely=0.125, anchor="center")

        tk.Label(
            title_frame,
            text="TITLE DEED",
            font=("times", (board_side - 2) // 56),
            bg=property_color,
        ).place(relx=0.5, rely=0.25, anchor="center")

        tk.Label(
            title_frame,
            text=property.upper(),
            font=("times", (board_side - 2) // 40),
            bg=property_color,
        ).place(relx=0.5, rely=0.65, anchor="center")

        tk.Button(
            title_frame,
            text="✕",
            font=("courier", (board_side - 2) // 60),
            bg=property_color,
            highlightthickness=0,
            border=0,
            activebackground=property_color,
            command=delete_property_frame,
        ).place(relx=1, rely=0, anchor="ne")

        canvas = tk.Canvas(
            property_frame,
            highlightthickness=0,
            width=(board_side - 2) // 2.25,
            height=(board_side - 2) // 2.6,
            bg="#F9FBFF",
        )
        canvas.place(relx=0.5, rely=0.625, anchor="center")
        canvas.update()
        y_coord = canvas.winfo_height() / 21

        ttk.Separator(canvas, orient="horizontal").place(
            relx=0.5, rely=0.69, anchor="center", relwidth=0.8
        )

        tk.Label(
            property_frame,
            text=f"Owner: {owner}",
            font=("times", (board_side - 2) // 46),
            fg=player_color,
            bg="#F9FBFF",
        ).place(relx=0.5, rely=0.25, anchor="center")

        tk.Button(
            property_frame,
            image=big_info_tag,
            border=0,
            highlightthickness=0,
            command=hotel_rules,
        ).place(x=35, rely=0.9, anchor="center")

        row_counter = -2
        for i, j in d[property].items():  # Placing and formatting Rent data on card
            row_counter += 1
            if row_counter == houses:
                canvas.create_text(
                    2,
                    y_coord - 2,
                    anchor="w",
                    text="▶",
                    font=("times", (board_side - 2) // 32),
                    fill=player_color,
                )
            if row_counter in [-1, 0]:  # rent, double rent
                canvas.create_text(
                    25,
                    y_coord,
                    anchor="w",
                    text=i,
                    font=("times", (board_side - 2) // 42),
                )
                canvas.create_text(
                    canvas.winfo_width() / 1.375,
                    y_coord,
                    text="₩",
                    angle=180,
                    font=("courier", (board_side - 2) // 42),
                )
                canvas.create_text(
                    canvas.winfo_width() - 25,
                    y_coord,
                    anchor="e",
                    text=str(j),
                    font=("times", (board_side - 2) // 42),
                )
            elif row_counter in [1, 2, 3, 4]:  # houses
                canvas.create_text(
                    25,
                    y_coord,
                    anchor="w",
                    text=i,
                    font=("times", (board_side - 2) // 42),
                    fill="green",
                )
                canvas.create_text(
                    canvas.winfo_width() / 1.375,
                    y_coord,
                    text="₩",
                    angle=180,
                    font=("courier", (board_side - 2) // 42),
                    fill="green",
                )
                canvas.create_text(
                    canvas.winfo_width() - 25,
                    y_coord,
                    anchor="e",
                    text=str(j),
                    font=("times", (board_side - 2) // 42),
                    fill="green",
                )
            elif row_counter == 5:  # hotel
                canvas.create_text(
                    25,
                    y_coord,
                    anchor="w",
                    text=i,
                    font=("times", (board_side - 2) // 42),
                    fill="red",
                )
                canvas.create_text(
                    canvas.winfo_width() / 1.375,
                    y_coord,
                    text="₩",
                    angle=180,
                    font=("courier", (board_side - 2) // 42),
                    fill="red",
                )
                canvas.create_text(
                    canvas.winfo_width() - 25,
                    y_coord,
                    anchor="e",
                    text=str(j),
                    font=("times", (board_side - 2) // 42),
                    fill="red",
                )
            elif row_counter == 6:  # mortgage
                canvas.create_text(
                    45,
                    y_coord,
                    anchor="w",
                    text=i,
                    font=("times", (board_side - 2) // 49),
                )
                canvas.create_text(
                    canvas.winfo_width() / 1.375,
                    y_coord,
                    text="₩",
                    angle=180,
                    font=("courier", (board_side - 2) // 49),
                )
                canvas.create_text(
                    canvas.winfo_width() - 35,
                    y_coord,
                    anchor="e",
                    text=str(j),
                    font=("times", (board_side - 2) // 49),
                )
            elif row_counter == 7:  # build house
                canvas.create_text(
                    45,
                    y_coord,
                    anchor="w",
                    text=i,
                    font=("times", (board_side - 2) // 49),
                    fill="green",
                )
                canvas.create_text(
                    canvas.winfo_width() / 1.375,
                    y_coord,
                    text="₩",
                    angle=180,
                    font=("courier", (board_side - 2) // 49),
                    fill="green",
                )
                canvas.create_text(
                    canvas.winfo_width() - 35,
                    y_coord,
                    anchor="e",
                    text=str(j),
                    font=("times", (board_side - 2) // 49),
                    fill="green",
                )
            elif row_counter == 8:  # build hotel
                canvas.create_text(
                    45,
                    y_coord,
                    anchor="w",
                    text=i,
                    font=("times", (board_side - 2) // 49),
                    fill="red",
                )
                canvas.create_text(
                    canvas.winfo_width() / 1.375,
                    y_coord,
                    text="₩",
                    angle=180,
                    font=("courier", (board_side - 2) // 49),
                    fill="red",
                )
                canvas.create_text(
                    canvas.winfo_width() - 35,
                    y_coord,
                    anchor="e",
                    text=str(j),
                    font=("times", (board_side - 2) // 49),
                    fill="red",
                )

            y_coord += canvas.winfo_height() / 10.25


property_frame = None


def property_click(event):
    if event.x in range(0, 200) and event.y in range(0, 200):
        print("blah")
        property_frame_popup("Mayfair")


def delete_property_frame():
    global property_frame
    property_frame.place_forget()
    property_frame = None


def player_frame_popup(player):
    player_frame = tk.Frame(
        main_frame, width=(board_side - 2) // 2.05, height=(board_side - 2) // 2.45
    )

    player_frame.place(relx=1, rely=0, anchor="ne")

    # scroll = ttk.Scrollbar(dataframe,orient=tk.VERTICAL)
    # scroll.place(relx=1,rely=0,anchor='ne',relheight=1)
    # scroll.config(command=listbox.yview)


bank_frame = tk.Frame(
    main_frame, width=(board_side - 2) // 2.05, height=(board_side - 2) // 2.45
)

bank_frame.place(relx=0, rely=0, anchor="nw")


def bank_frame_popup():
    global bank_frame


def action_frame_popup(action):
    action_frame = tk.Frame(
        main_frame, width=(board_side - 2) // 2.05, height=(board_side - 2) // 1.75
    )

    action_frame.place(relx=0, rely=1, anchor="sw")


def roll_dice():
    global check, player, current_move
    player = dictionary[check % 4]
    mixer.music.load("Assets/diceroll.mp3")
    mixer.music.play(loops=0)
    dice_roll = random.randint(1, 6), random.randint(1, 6)
    for i in range(18):
        dice_spot1.configure(image=die_dict[random.randint(1, 6)])
        dice_spot2.configure(image=die_dict[random.randint(1, 6)])
        dice_spot1.update()
        dice_spot2.update()
        sleep(0.12)
    dice_spot1.configure(image=die_dict[dice_roll[0]])
    dice_spot2.configure(image=die_dict[dice_roll[1]])
    current_move = sum(dice_roll)
    move_token(current_move)
    check += 1


def move_token(move):
    x, y = float(player[1].place_info()["x"]), float(player[1].place_info()["y"])
    for i in range(1, move + 1):
        player[2] += 1
        position = player[2] % 40
        if player[1] is red_token:
            if position in range(1, 10):
                x -= property_width
            elif position == 10:
                if injail:
                    x -= 1.2 * property_width
                    y -= 0.4 * property_width
                else:
                    x -= 1.75 * property_width
            elif position == 11:
                x += 0.6 * property_width
                y -= 1.5 * property_width
            elif position in range(12, 20):
                y -= property_width
            elif position == 20:
                x += 0.4 * property_width
                y -= 1.1 * property_width
            elif position in range(21, 30):
                x += property_width
            elif position == 30:
                x += 1.2 * property_width
                y += 0.4 * property_width
            elif position in range(31, 40):
                y += property_width
            else:
                x = board_side - 1.2 * property_width
                y = board_side - 0.75 * property_width
        elif player[1] is green_token:
            if position in range(1, 10):
                x -= property_width
            elif position == 10:
                if injail:
                    x -= 1.2 * property_width
                    y -= 0.4 * property_width
                else:
                    x -= 2.1 * property_width
                    y -= 0.4 * property_width
            elif position == 11:
                x += 0.6 * property_width
                y -= 0.75 * property_width
            elif position in range(12, 20):
                y -= property_width
            elif position == 20:
                x += 0.05 * property_width
                y -= 1.45 * property_width
            elif position in range(21, 30):
                x += property_width
            elif position == 30:
                x += 1.55 * property_width
                y += 0.07 * property_width
            elif position in range(31, 40):
                y += property_width
            else:
                x = board_side - 0.85 * property_width
                y = board_side - 0.75 * property_width
        elif player[1] is blue_token:
            if position in range(1, 10):
                x -= property_width
            elif position == 10:
                if injail:
                    x -= 1.2 * property_width
                    y -= 0.4 * property_width
                else:
                    x -= 1.3 * property_width
                    y += 0.2 * property_width
            elif position == 11:
                x -= 0.2 * property_width
                y -= 2.05 * property_width
            elif position in range(12, 20):
                y -= property_width
            elif position == 20:
                x += 0.74 * property_width
                y -= 1.44 * property_width
            elif position in range(21, 30):
                x += property_width
            elif position == 30:
                x += 1.53 * property_width
                y += 0.75 * property_width
            elif position in range(31, 40):
                y += property_width
            else:
                x = board_side - 1.2 * property_width
                y = board_side - 0.4 * property_width
        elif player[1] is yellow_token:
            if position in range(1, 10):
                x -= property_width
            elif position == 10:
                if injail:
                    x -= 1.2 * property_width
                    y -= 0.4 * property_width
                else:
                    x -= 1.2 * property_width
                    y += 0.2 * property_width
            elif position == 11:
                x -= 0.65 * property_width
                y -= 1.7 * property_width
            elif position in range(12, 20):
                y -= property_width
            elif position == 20:
                x += 0.4 * property_width
                y -= 1.8 * property_width
            elif position in range(21, 30):
                x += property_width
            elif position == 30:
                x += 1.87 * property_width
                y += 0.43 * property_width
            elif position in range(31, 40):
                y += property_width
            else:
                x = board_side - 0.85 * property_width
                y = board_side - 0.4 * property_width

        player[1].place(x=x, y=y)
        player[1].update()
        sleep(0.2)


board_canvas.bind("<Button-1>", property_click)

monopoly_window.mainloop()
