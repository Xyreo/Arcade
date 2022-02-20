import tkinter as tk
import tkinter.ttk as ttk
from PIL import ImageTk, Image, ImageOps

root = tk.Tk()
root.title("Monopoly")
root.geometry("1250x800")

s=ttk.Style()
s.configure('my.TButton',font=("Helvetica",30))
   
boardIMG = ImageTk.PhotoImage(
    ImageOps.expand(
        Image.open("Images/BoardIMG.jpg"),border=3).resize((750, 750)))

canvas = tk.Canvas(root, width=750, height=750) 
canvas.place(x=10,y=25)
canvas.create_image(2,2,image=boardIMG,anchor='nw')

but = ttk.Button(canvas, text="Roll Dice",style="my.TButton").place(x=287.5,y=349,width=175,height=52)


root.mainloop()
