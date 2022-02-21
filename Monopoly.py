import tkinter as tk
import tkinter.ttk as ttk
from PIL import ImageTk, Image, ImageOps

root = tk.Tk()
root.title("Monopoly")
root.resizable(False,False)
root.config(bg='')

screenwidth = root.winfo_screenwidth()-100
screenheight = root.winfo_screenheight()-100
m = root.winfo_screenwidth()//2 - screenwidth//2
n = (root.winfo_screenheight()-70)//2 - screenheight//2
root.geometry(f"{screenwidth}x{screenheight}+{m}+{n}")

s=ttk.Style()
s.configure('my.TButton',font=("Helvetica",20))

boardside = screenheight-65
propwidth = boardside/12.2

canvas = tk.Canvas(root, width=boardside, height=boardside) 
canvas.place(x=10,y=32.5)

boardIMG = ImageTk.PhotoImage(
    ImageOps.expand(
        Image.open("Images/BoardIMG.jpg").resize((boardside,boardside),Image.ANTIALIAS)))

canvas.create_image(2,2,image=boardIMG,anchor='nw')

infoIMG = ImageTk.PhotoImage(file="Images/Info.png")

def propertypop(property):
    global popup
    if popup is None:
        popup = tk.Toplevel()
        popup.title(property)
        popup.geometry(f"300x350")
        popup.resizable(False,False)
        popup.protocol('WM_DELETE_WINDOW', removepop)

        #canvas.create_text(300,300,text="₩",angle=180)
    else:
        removepop()
        propertypop(property)

def removepop():
    global popup
    popup.destroy()
    popup = None

#Info Button For Each Property

posvar = boardside - propwidth/5.5

oldkent = tk.Button(canvas, image = infoIMG,borderwidth=0,command= lambda: propertypop("Old Kent Road"))
oldkent.place(x=posvar - 1.6*propwidth,y=posvar,anchor='center')

whitechapel = tk.Button(canvas, image = infoIMG,borderwidth=0,command= lambda: propertypop("Whitechapel Road"))
whitechapel.place(x=posvar - 3.6*propwidth,y=posvar,anchor='center')

kingscross = tk.Button(canvas, image = infoIMG,borderwidth=0,command= lambda: propertypop("Kings Cross Station"))
kingscross.place(x=posvar - 5.6*propwidth ,y=posvar,anchor='center')

angel = tk.Button(canvas, image = infoIMG,borderwidth=0,command= lambda: propertypop("The Angel, Islington"))
angel.place(x=posvar - 6.6*propwidth ,y=posvar,anchor='center')

euston = tk.Button(canvas, image = infoIMG,borderwidth=0,command= lambda: propertypop("Euston Road"))
euston.place(x=posvar - 8.6*propwidth,y=posvar,anchor='center')

pentonville = tk.Button(canvas, image = infoIMG,borderwidth=0,command= lambda: propertypop("Pentonville Road"))
pentonville.place(x=posvar-9.6*propwidth,y=posvar,anchor='center')

jail = tk.Button(canvas, image = infoIMG,borderwidth=0,command= lambda: propertypop("Jail"))
jail.place(x=posvar-11.8*propwidth ,y=posvar,anchor='center')

pallmall = tk.Button(canvas, image = infoIMG,borderwidth=0,command= lambda: propertypop("Pall Mall"))
pallmall.place(x=posvar - 11.8*propwidth ,y=posvar - 1.6*propwidth,anchor='center')

electric = tk.Button(canvas, image = infoIMG,borderwidth=0,command= lambda: propertypop("Electric Company"))
electric.place(x=posvar - 11.8*propwidth ,y=posvar - 2.6*propwidth,anchor='center')

whitehall = tk.Button(canvas, image = infoIMG,borderwidth=0,command= lambda: propertypop("Whitehall"))
whitehall.place(x=posvar - 11.8*propwidth ,y=posvar - 3.6*propwidth,anchor='center')

northumbld = tk.Button(canvas, image = infoIMG,borderwidth=0,command= lambda: propertypop("Northumbl'd Avenue"))
northumbld.place(x=posvar - 11.8*propwidth ,y=posvar - 4.6*propwidth,anchor='center')

marleybone = tk.Button(canvas, image = infoIMG,borderwidth=0,command= lambda: propertypop("Marylebone Station"))
marleybone.place(x=posvar - 11.8*propwidth ,y=posvar - 5.6*propwidth,anchor='center')

bow = tk.Button(canvas, image = infoIMG,borderwidth=0,command= lambda: propertypop("Bow Street"))
bow.place(x=posvar - 11.8*propwidth ,y=posvar - 6.6*propwidth,anchor='center')

marlborough = tk.Button(canvas, image = infoIMG,borderwidth=0,command= lambda: propertypop("Marlborough Street"))
marlborough.place(x=posvar - 11.8*propwidth ,y=posvar - 8.6*propwidth,anchor='center')

vine = tk.Button(canvas, image = infoIMG,borderwidth=0,command= lambda: propertypop("Vine Street"))
vine.place(x=posvar - 11.8*propwidth,y=posvar - 9.6*propwidth,anchor='center')

strand = tk.Button(canvas, image = infoIMG,borderwidth=0,command= lambda: propertypop("Strand"))
strand.place(x=posvar-10.2*propwidth,y=posvar - 11.8*propwidth,anchor='center')

fleet = tk.Button(canvas, image = infoIMG,borderwidth=0,command= lambda: propertypop("Fleet Street"))
fleet.place(x=posvar-8.2*propwidth,y=posvar - 11.8*propwidth,anchor='center')

trafalgar = tk.Button(canvas, image = infoIMG,borderwidth=0,command= lambda: propertypop("Trafalgar Square"))
trafalgar.place(x=posvar-7.2*propwidth ,y=posvar - 11.8*propwidth,anchor='center')

fenchurch = tk.Button(canvas, image = infoIMG,borderwidth=0,command= lambda: propertypop("Fenchurch St. Station"))
fenchurch.place(x=posvar- 6.2*propwidth,y=posvar - 11.8*propwidth,anchor='center')

leicester = tk.Button(canvas, image = infoIMG,borderwidth=0,command= lambda: propertypop("Leicester Square"))
leicester.place(x=posvar- 5.2*propwidth,y=posvar - 11.8*propwidth,anchor='center')

coventry = tk.Button(canvas, image = infoIMG,borderwidth=0,command= lambda: propertypop("Coventry Street"))
coventry.place(x=posvar- 4.2*propwidth,y=posvar - 11.8*propwidth,anchor='center')

water = tk.Button(canvas, image = infoIMG,borderwidth=0,command= lambda: propertypop("Water Works"))
water.place(x=posvar- 3.2*propwidth,y=posvar - 11.8*propwidth,anchor='center')

piccadilly = tk.Button(canvas, image = infoIMG,borderwidth=0,command= lambda: propertypop("Piccadilly"))
piccadilly.place(x=posvar- 2.2*propwidth,y=posvar - 11.8*propwidth,anchor='center')

gotojail = tk.Button(canvas, image = infoIMG,borderwidth=0,command= lambda: propertypop("Go To Jail"))
gotojail.place(x=posvar,y=posvar - 11.8*propwidth,anchor='center')

regent = tk.Button(canvas, image = infoIMG,borderwidth=0,command= lambda: propertypop("Regent Street"))
regent.place(x=posvar,y=posvar - 10.2*propwidth,anchor='center')

oxford = tk.Button(canvas, image = infoIMG,borderwidth=0,command= lambda: propertypop("Oxford Street"))
oxford.place(x=posvar,y=posvar - 9.2*propwidth,anchor='center')

bond = tk.Button(canvas, image = infoIMG,borderwidth=0,command= lambda: propertypop("Bond Street"))
bond.place(x=posvar,y=posvar - 7.2*propwidth,anchor='center')

liverpool = tk.Button(canvas, image = infoIMG,borderwidth=0,command= lambda: propertypop("Liverpool St. Station"))
liverpool.place(x=posvar,y=posvar - 6.2*propwidth,anchor='center')

parklane = tk.Button(canvas, image = infoIMG,borderwidth=0,command= lambda: propertypop("Park Lane"))
parklane.place(x=posvar,y=posvar - 4.2*propwidth,anchor='center')

mayfair = tk.Button(canvas, image = infoIMG,borderwidth=0,command= lambda: propertypop("Mayfair"))
mayfair.place(x=posvar,y=posvar - 2.2*propwidth,anchor='center')

popup = None


roll = ttk.Button(canvas, text="Roll Dice",style="my.TButton")
roll.place(x=boardside/2 - roll.winfo_width() ,y=boardside/2 - roll.winfo_height(),anchor='center')


root.mainloop()