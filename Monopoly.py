import tkinter as tk
import tkinter.ttk as ttk
from PIL import ImageTk, Image, ImageOps

root = tk.Tk()
root.title("Monopoly")
root.wm_attributes('-transparentcolor', '#1b6e81')

screenwidth = root.winfo_screenwidth()-14
screenheight = root.winfo_screenheight()-44
root.geometry(f"{screenwidth}x{screenheight}")

s=ttk.Style()
s.configure('my.TButton',font=("Helvetica",20))

boardside = screenheight-65
a = boardside/12.2

boardIMG = ImageTk.PhotoImage(
    ImageOps.expand(
        Image.open("Images/BoardIMG.jpg").resize((boardside,boardside),Image.ANTIALIAS)))

canvas = tk.Canvas(root, width=boardside, height=boardside) 
canvas.place(x=10,y=32.5)
canvas.create_image(2,2,image=boardIMG,anchor='nw')

roll = ttk.Button(canvas, text="Roll Dice",style="my.TButton")
roll.place(x=boardside/2 - roll.winfo_width() ,y=boardside/2 - roll.winfo_height(),anchor='center')

passgo = tk.Button(canvas, text='hi',bg='#1b6e81')
passgo.place(x=boardside - (a+0.6*a) ,y=boardside-(a+0.6*a), width=a+0.6*a, height=a+0.6*a)


root.mainloop()
 