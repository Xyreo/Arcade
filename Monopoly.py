import tkinter as tk
import tkinter.ttk as ttk
from PIL import ImageTk, Image, ImageOps
import random
from time import sleep
from pygame import mixer

root = tk.Tk()
root.withdraw()
root.deiconify()
root.title("Monopoly")
root.resizable(False,False)
root.config(bg='')

mixer.init()

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
        Image.open("Assets/BoardIMG.jpg").resize((boardside,boardside),Image.ANTIALIAS)))

canvas.create_image(2,2,image=boardIMG,anchor='nw')

infoIMG = ImageTk.PhotoImage(file="Assets/Info.png")

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

dice1 = ImageTk.PhotoImage(Image.open("Assets/dice1.png"))
dice2 = ImageTk.PhotoImage(Image.open("Assets/dice2.png"))
dice3 = ImageTk.PhotoImage(Image.open("Assets/dice3.png"))
dice4 = ImageTk.PhotoImage(Image.open("Assets/dice4.png"))
dice5 = ImageTk.PhotoImage(Image.open("Assets/dice5.png"))
dice6 = ImageTk.PhotoImage(Image.open("Assets/dice6.png"))

diedict = dict(zip((1,2,3,4,5,6),(dice1,dice2,dice3,dice4,dice5,dice6)))


redimg = ImageTk.PhotoImage(Image.open("Assets/red.png"))
greenimg = ImageTk.PhotoImage(Image.open("Assets/green.png"))
blueimg = ImageTk.PhotoImage(Image.open("Assets/blue.png"))
yellowimg = ImageTk.PhotoImage(Image.open("Assets/yellow.png"))

red = tk.Button(canvas, image = redimg,border=0,command= lambda: propertypop("Liverpool St. Station"))
red.place(x=boardside-1.2*propwidth,y=boardside-0.75*propwidth,anchor='center')

green = tk.Button(canvas, image = greenimg,border=0,command= lambda: propertypop("Liverpool St. Station"))
green.place(x=boardside-0.85*propwidth,y=boardside-0.75*propwidth,anchor='center')

blue = tk.Button(canvas, image = blueimg,border=0,command= lambda: propertypop("Liverpool St. Station"))
blue.place(x=boardside-1.2*propwidth,y=boardside-0.4*propwidth,anchor='center')

yellow = tk.Button(canvas, image = yellowimg,border=0,command= lambda: propertypop("Liverpool St. Station"))
yellow.place(x=boardside-0.85*propwidth,y=boardside-0.4*propwidth,anchor='center')

player = ["playername",green,0]
othermove = 10
def rolldice():
    mixer.music.load("Assets/diceroll.mp3")
    mixer.music.play(loops=0)
    diceroll = random.randint(1,6),random.randint(1,6)
    # diceroll = 5,6
    for i in range(18):
        die1.configure(image=diedict[random.randint(1,6)])
        die2.configure(image=diedict[random.randint(1,6)])
        die1.update()
        die2.update()
        sleep(0.12)
    die1.configure(image=diedict[diceroll[0]])
    die2.configure(image=diedict[diceroll[1]])
    currmove = sum(diceroll)
    x,y=float(player[1].place_info()['x']),float(player[1].place_info()['y'])
    for i in range(1,currmove+1):
        player[2]+=1
        posi = player[2]%40
        if player[1] is red:
            if posi in range(1,10):
                x-=propwidth
            elif posi==10:
                x-=1.75*propwidth
            elif posi==11:
                x+=0.4*propwidth
                y-=1.6*propwidth
            elif posi in range(12,20):
                y-=propwidth
            elif posi==20:
                x+=0.6*propwidth
                y-=propwidth
            elif posi in range(21,30):
                x+=propwidth
            elif posi == 30:
                x+=1.2*propwidth
                y+=0.4*propwidth
            elif posi in range(31,40):
                y+=propwidth
            else:
                x-=0.43*propwidth
                y+=1.2*propwidth
        elif player[1] is green:
            if posi in range(1,10):
                x-=propwidth
            elif posi==10:
                x-=2.1*propwidth
                y-=0.4*propwidth
            elif posi==11:
                x+=0.4*propwidth
                y-=0.9*propwidth
            elif posi in range(12,20):
                y-=propwidth
            elif posi==20:
                x+=0.6*propwidth
                y-=1.75*propwidth
            elif posi in range(21,30):
                x+=propwidth
            elif posi == 30:
                x+=1.5*propwidth
                y+=0.4*propwidth
            elif posi in range(31,40):
                y+=propwidth
            else:
                x-=0.43*propwidth
                y+=1.2*propwidth

        player[1].place(x=x,y=y)
        player[1].update()
        sleep(0.2)

roll = ttk.Button(canvas, text="Roll Dice",style="my.TButton",command=rolldice)
roll.place(x=boardside/2 ,y=boardside/2 ,anchor='center')
roll.update()

die1 = tk.Label(canvas,image=dice6,borderwidth=0)
die1.place(x = boardside/2 - roll.winfo_width()/2.5, y= boardside/2 - roll.winfo_height()/1.5,anchor='sw')

die2 = tk.Label(canvas,image=dice6,borderwidth=0)
die2.place(x = boardside/2 + roll.winfo_width()/2.5, y= boardside/2 - roll.winfo_height()/1.5,anchor='se')



root.mainloop()