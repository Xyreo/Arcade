import tkinter as tk
from tkinter import messagebox
import tkinter.ttk as ttk
from PIL import ImageTk, Image, ImageOps
import random
from time import sleep
from pygame import mixer
import threading


root = tk.Tk()
mainwin = tk.Toplevel()
mainwin.title("Monopoly")
mainwin.resizable(False,False)
mainwin.config(bg='white')
mainwin.protocol('WM_DELETE_WINDOW', root.destroy)

screenwidth = mainwin.winfo_screenwidth()-100
screenheight = mainwin.winfo_screenheight()-100
m = mainwin.winfo_screenwidth()//2 - screenwidth//2
n = (mainwin.winfo_screenheight()-70)//2 - screenheight//2
mainwin.geometry(f"{screenwidth}x{screenheight}+{m}+{n}")

mainwin.withdraw()
def monopoly():
    global mainwin
    mainwin.deiconify()
    root.withdraw()

start = ttk.Button(root,text='START',command = monopoly).pack()

mixer.init()

boardside = screenheight-65
propwidth = boardside/12.2

s=ttk.Style()
s.configure('my.TButton',font=("times",int(propwidth/3)))



boardframe = tk.Frame(mainwin, width=boardside, height=boardside)
boardframe.place(relx=0.01,rely=0.04,anchor='nw')

boardIMG = ImageTk.PhotoImage(ImageOps.expand(Image.open("Assets/BoardIMG.jpg").resize((boardside,boardside),Image.ANTIALIAS)))
img = ttk.Label(boardframe,image=boardIMG).place(relx=0.499,rely=0.499,anchor='center')

infoIMG = ImageTk.PhotoImage(ImageOps.expand(Image.open("Assets/Info.png").resize((int(propwidth/5.5),int(propwidth/5.5)),Image.ANTIALIAS)))

mainframe = tk.Frame(mainwin, width = boardside-2, height = boardside-2, background='white')
mainframe.place(relx=0.99,rely=0.04,anchor='ne')

propertyframe = tk.Frame(mainframe,width = (boardside-2)//2.05, height = (boardside-2)//1.75,bg='#F9FBFF',highlightthickness=2,highlightbackground='black')
propertyframe.place(relx=1,rely=1,anchor='se')

playerframe = tk.Frame(mainframe, width = (boardside-2)//2.05, height = (boardside-2)//2.45)
playerframe.place(relx=1,rely=0,anchor='ne')

bankframe = tk.Frame(mainframe, width = (boardside-2)//2.05, height = (boardside-2)//2.45)
bankframe.place(relx=0,rely=0,anchor='nw')

actionframe = tk.Frame(mainframe, width = (boardside-2)//2.05, height = (boardside-2)//1.75)
actionframe.place(relx=0,rely=1,anchor='sw')

s1 = ttk.Style()
s1.configure('tvstyle.T',background='black')

# scroll = ttk.Scrollbar(dataframe,orient=tk.VERTICAL)
# scroll.place(relx=1,rely=0,anchor='ne',relheight=1)
# scroll.config(command=listbox.yview)

hotelinfoIMG = ImageTk.PhotoImage(ImageOps.expand(Image.open("Assets/hotelrulesinfo.png").resize((int(propwidth/2),int(propwidth/2)),Image.ANTIALIAS)))

def hotelrule():
    hrule = messagebox.showinfo("HOTEL RULES")


def propertyframepopup(property):
    global propertyframe
    #TODO: #change colour according to property

    titleframe = tk.Frame(propertyframe,width = (boardside-2)//2.25, height = (boardside - 2)//10,bg='#016cbf',highlightthickness=2,highlightbackground='black')
    titleframe.place(relx=0.5,rely = 0.125,anchor = 'center')

    tk.Label(titleframe,text="TITLE DEED",font=("times",(boardside-2)//52),bg='#016cbf').place(relx=0.5,rely=0.25,anchor='center')

    tk.Label(titleframe,text=property.upper(),font=("times",(boardside-2)//42),bg='#016cbf').place(relx=0.5,rely=0.65,anchor='center')


    canvas = tk.Canvas(propertyframe,highlightthickness=0,width = (boardside-2)//2.25, height = (boardside - 2)//2.6,bg='#F9FBFF')
    canvas.place(relx=0.5,rely = 0.625,anchor ='center')
    canvas.update()
    centery = canvas.winfo_height()/21
    d = {}

    d["Mayfair"] = dict(zip(
        ["Rent",'With Color Set','With 1 House','With 2 Houses','With 3 Houses','With 4 Houses','With Hotel','Mortgage Value','House Cost','Hotel Cost'],
        [50,100,200,600,1400,1700,2000,200,200,200]))#get from db
    
    owner = "Player 1"#get from db
    houses = 4#get from db[-1 to 5]
    counter  = -2

    ttk.Separator(canvas,orient='horizontal').place(relx=0.5,rely=0.69,anchor="center",relwidth=0.8)


    tk.Label(propertyframe,text=f"Owner: {owner}",font=("times",(boardside-2)//46),fg="red",bg='#F9FBFF').place(relx=0.5,rely=0.25,anchor='center')
                                                                                    #change fg color according to player color


    tk.Button(propertyframe, image = hotelinfoIMG,border=0,highlightthickness=0,command= hotelrule).place(x=35,rely=0.9,anchor='center')
    #TODO: Different for utility and station
    for i,j in d[property].items():
        counter+=1
        if counter==houses:
            canvas.create_text(2,centery-2,anchor='w',text="▶",font=("times",(boardside - 2)//32),fill='red')#change fill color according to player color
        if counter==5:
            canvas.create_text(25,centery,anchor='w',text=i,font=("times",(boardside - 2)//42),fill='red')
            canvas.create_text(canvas.winfo_width()/1.375,centery,text="₩",angle=180,font=("courier",(boardside - 2)//42),fill='red')
            canvas.create_text(canvas.winfo_width()-25,centery,anchor='e',text=str(j),font=("times",(boardside - 2)//42),fill='red')
        elif counter in [1,2,3,4]:
            canvas.create_text(25,centery,anchor='w',text=i,font=("times",(boardside - 2)//42),fill='green')
            canvas.create_text(canvas.winfo_width()/1.375,centery,text="₩",angle=180,font=("courier",(boardside - 2)//42),fill='green')
            canvas.create_text(canvas.winfo_width()-25,centery,anchor='e',text=str(j),font=("times",(boardside - 2)//42),fill='green')
        elif counter==6:
            canvas.create_text(45,centery,anchor='w',text=i,font=("times",(boardside - 2)//49),)
            canvas.create_text(canvas.winfo_width()/1.375,centery,text="₩",angle=180,font=("courier",(boardside - 2)//49))
            canvas.create_text(canvas.winfo_width()-45,centery,anchor='e',text=str(j),font=("times",(boardside - 2)//49))
        elif counter==7:
            canvas.create_text(45,centery,anchor='w',text=i,font=("times",(boardside - 2)//49),fill='green')
            canvas.create_text(canvas.winfo_width()/1.375,centery,text="₩",angle=180,font=("courier",(boardside - 2)//49),fill='green')
            canvas.create_text(canvas.winfo_width()-45,centery,anchor='e',text=str(j),font=("times",(boardside - 2)//49),fill='green')
        elif counter==8:
            canvas.create_text(45,centery,anchor='w',text=i,font=("times",(boardside - 2)//49),fill='red')
            canvas.create_text(canvas.winfo_width()/1.375,centery,text="₩",angle=180,font=("courier",(boardside - 2)//49),fill='red')
            canvas.create_text(canvas.winfo_width()-45,centery,anchor='e',text=str(j),font=("times",(boardside - 2)//49),fill='red')
        else:
            canvas.create_text(25,centery,anchor='w',text=i,font=("times",(boardside - 2)//42),)
            canvas.create_text(canvas.winfo_width()/1.375,centery,text="₩",angle=180,font=("courier",(boardside - 2)//42))
            canvas.create_text(canvas.winfo_width()-25,centery,anchor='e',text=str(j),font=("times",(boardside - 2)//42))
        centery+=canvas.winfo_height()/10.25

propertyframepopup("Mayfair")

def playerpop(player):
    global playerpopup
    #TODO: Create custom titlebar
    if playerpopup is None:
        playerpopup = tk.Toplevel()
        playerpopup.title(player)
        playerpopup.resizable(False,False)
        playerpopup.overrideredirect(1)
        root_x = mainwin.winfo_rootx()
        root_y = mainwin.winfo_rooty()
        playerpopup.geometry(f"{(screenwidth-boardside-20)//2 - 40}x{boardside//2}+{int(root_x+boardside+(screenwidth-boardside-20)//2 + 40)}+{int(root_y+32.5)}")
        playerpopup.attributes('-topmost', 1)

def minimize(event):
    global propertypopup,playerpopup
    if event.widget is mainwin:
        if propertypopup:
            propertypopup.withdraw()
        if playerpopup:
            playerpopup.withdraw()

def maximize(event):
    global propertypopup,playerpopup
    if event.widget is mainwin:
        if propertypopup:
            propertypopup.deiconify()
            propertypopup.attributes('-topmost', 1)
        if playerpopup:
            playerpopup.deiconify()
            playerpopup.attributes('-topmost', 1)


#region#Info Button For Each Property
posvar = boardside - propwidth/5.5

oldkent = tk.Button(boardframe, image = infoIMG,border=0,highlightthickness=0,command= lambda: propertyframepopup("Old Kent Road"))
oldkent.place(x=posvar - 1.6*propwidth,y=posvar,anchor='center')

whitechapel = tk.Button(boardframe, image = infoIMG,border=0,highlightthickness=0,command= lambda: propertyframepopup("Whitechapel Road"))
whitechapel.place(x=posvar - 3.6*propwidth,y=posvar,anchor='center')

kingscross = tk.Button(boardframe, image = infoIMG,border=0,highlightthickness=0,command= lambda: propertyframepopup("Kings Cross Station"))
kingscross.place(x=posvar - 5.6*propwidth ,y=posvar,anchor='center')

angel = tk.Button(boardframe, image = infoIMG,border=0,highlightthickness=0,command= lambda: propertyframepopup("The Angel, Islington"))
angel.place(x=posvar - 6.6*propwidth ,y=posvar,anchor='center')

euston = tk.Button(boardframe, image = infoIMG,border=0,highlightthickness=0,command= lambda: propertyframepopup("Euston Road"))
euston.place(x=posvar - 8.6*propwidth,y=posvar,anchor='center')

pentonville = tk.Button(boardframe, image = infoIMG,border=0,highlightthickness=0,command= lambda: propertyframepopup("Pentonville Road"))
pentonville.place(x=posvar-9.6*propwidth,y=posvar,anchor='center')

jail = tk.Button(boardframe, image = infoIMG,border=0,highlightthickness=0,command= lambda: propertyframepopup("Jail"))
jail.place(x=posvar-11.8*propwidth ,y=posvar,anchor='center')

pallmall = tk.Button(boardframe, image = infoIMG,border=0,highlightthickness=0,command= lambda: propertyframepopup("Pall Mall"))
pallmall.place(x=posvar - 11.825*propwidth ,y=posvar - 1.6*propwidth,anchor='center')

electric = tk.Button(boardframe, image = infoIMG,border=0,highlightthickness=0,command= lambda: propertyframepopup("Electric Company"))
electric.place(x=posvar - 11.825*propwidth ,y=posvar - 2.6*propwidth,anchor='center')

whitehall = tk.Button(boardframe, image = infoIMG,border=0,highlightthickness=0,command= lambda: propertyframepopup("Whitehall"))
whitehall.place(x=posvar - 11.825*propwidth ,y=posvar - 3.6*propwidth,anchor='center')

northumbld = tk.Button(boardframe, image = infoIMG,border=0,highlightthickness=0,command= lambda: propertyframepopup("Northumbl'd Avenue"))
northumbld.place(x=posvar - 11.825*propwidth ,y=posvar - 4.6*propwidth,anchor='center')

marleybone = tk.Button(boardframe, image = infoIMG,border=0,highlightthickness=0,command= lambda: propertyframepopup("Marylebone Station"))
marleybone.place(x=posvar - 11.825*propwidth ,y=posvar - 5.6*propwidth,anchor='center')

bow = tk.Button(boardframe, image = infoIMG,border=0,highlightthickness=0,command= lambda: propertyframepopup("Bow Street"))
bow.place(x=posvar - 11.825*propwidth ,y=posvar - 6.6*propwidth,anchor='center')

marlborough = tk.Button(boardframe, image = infoIMG,border=0,highlightthickness=0,command= lambda: propertyframepopup("Marlborough Street"))
marlborough.place(x=posvar - 11.825*propwidth ,y=posvar - 8.6*propwidth,anchor='center')

vine = tk.Button(boardframe, image = infoIMG,border=0,highlightthickness=0,command= lambda: propertyframepopup("Vine Street"))
vine.place(x=posvar - 11.825*propwidth,y=posvar - 9.6*propwidth,anchor='center')

strand = tk.Button(boardframe, image = infoIMG,border=0,highlightthickness=0,command= lambda: propertyframepopup("Strand"))
strand.place(x=posvar-10.21*propwidth,y=posvar - 11.825*propwidth,anchor='center')

fleet = tk.Button(boardframe, image = infoIMG,border=0,highlightthickness=0,command= lambda: propertyframepopup("Fleet Street"))
fleet.place(x=posvar-8.21*propwidth,y=posvar - 11.825*propwidth,anchor='center')

trafalgar = tk.Button(boardframe, image = infoIMG,border=0,highlightthickness=0,command= lambda: propertyframepopup("Trafalgar Square"))
trafalgar.place(x=posvar-7.21*propwidth ,y=posvar - 11.825*propwidth,anchor='center')

fenchurch = tk.Button(boardframe, image = infoIMG,border=0,highlightthickness=0,command= lambda: propertyframepopup("Fenchurch St. Station"))
fenchurch.place(x=posvar- 6.21*propwidth,y=posvar - 11.825*propwidth,anchor='center')

leicester = tk.Button(boardframe, image = infoIMG,border=0,highlightthickness=0,command= lambda: propertyframepopup("Leicester Square"))
leicester.place(x=posvar- 5.21*propwidth,y=posvar - 11.825*propwidth,anchor='center')

coventry = tk.Button(boardframe, image = infoIMG,border=0,highlightthickness=0,command= lambda: propertyframepopup("Coventry Street"))
coventry.place(x=posvar- 4.21*propwidth,y=posvar - 11.825*propwidth,anchor='center')

water = tk.Button(boardframe, image = infoIMG,border=0,highlightthickness=0,command= lambda: propertyframepopup("Water Works"))
water.place(x=posvar- 3.21*propwidth,y=posvar - 11.825*propwidth,anchor='center')

piccadilly = tk.Button(boardframe, image = infoIMG,border=0,highlightthickness=0,command= lambda: propertyframepopup("Piccadilly"))
piccadilly.place(x=posvar- 2.21*propwidth,y=posvar - 11.825*propwidth,anchor='center')

gotojail = tk.Button(boardframe, image = infoIMG,border=0,highlightthickness=0,command= lambda: propertyframepopup("Go To Jail"))
gotojail.place(x=posvar,y=posvar - 11.825*propwidth,anchor='center')

regent = tk.Button(boardframe, image = infoIMG,border=0,highlightthickness=0,command= lambda: propertyframepopup("Regent Street"))
regent.place(x=posvar,y=posvar - 10.2*propwidth,anchor='center')

oxford = tk.Button(boardframe, image = infoIMG,border=0,highlightthickness=0,command= lambda: propertyframepopup("Oxford Street"))
oxford.place(x=posvar,y=posvar - 9.2*propwidth,anchor='center')

bond = tk.Button(boardframe, image = infoIMG,border=0,highlightthickness=0,command= lambda: propertyframepopup("Bond Street"))
bond.place(x=posvar,y=posvar - 7.2*propwidth,anchor='center')

liverpool = tk.Button(boardframe, image = infoIMG,border=0,highlightthickness=0,command= lambda: propertyframepopup("Liverpool St. Station"))
liverpool.place(x=posvar,y=posvar - 6.2*propwidth,anchor='center')

parklane = tk.Button(boardframe, image = infoIMG,border=0,highlightthickness=0,command= lambda: propertyframepopup("Park Lane"))
parklane.place(x=posvar,y=posvar - 4.2*propwidth,anchor='center')

mayfair = tk.Button(boardframe, image = infoIMG,border=0,highlightthickness=0,command= lambda: propertyframepopup("Mayfair"))
mayfair.place(x=posvar,y=posvar - 2.2*propwidth,anchor='center')

propertypopup = None
#endregion

#region#Dice and tokens
dice1 = ImageTk.PhotoImage(ImageOps.expand(Image.open("Assets/dice1.png").resize((int(0.9*propwidth),int(0.9*propwidth)),Image.ANTIALIAS)))
dice2 = ImageTk.PhotoImage(ImageOps.expand(Image.open("Assets/dice2.png").resize((int(0.9*propwidth),int(0.9*propwidth)),Image.ANTIALIAS)))
dice3 = ImageTk.PhotoImage(ImageOps.expand(Image.open("Assets/dice3.png").resize((int(0.9*propwidth),int(0.9*propwidth)),Image.ANTIALIAS)))
dice4 = ImageTk.PhotoImage(ImageOps.expand(Image.open("Assets/dice4.png").resize((int(0.9*propwidth),int(0.9*propwidth)),Image.ANTIALIAS)))
dice5 = ImageTk.PhotoImage(ImageOps.expand(Image.open("Assets/dice5.png").resize((int(0.9*propwidth),int(0.9*propwidth)),Image.ANTIALIAS)))
dice6 = ImageTk.PhotoImage(ImageOps.expand(Image.open("Assets/dice6.png").resize((int(0.9*propwidth),int(0.9*propwidth)),Image.ANTIALIAS)))

diedict = dict(zip((1,2,3,4,5,6),(dice1,dice2,dice3,dice4,dice5,dice6)))


redimg = ImageTk.PhotoImage(ImageOps.expand(Image.open("Assets/red.png").resize((boardside//39,boardside//39),Image.ANTIALIAS)))
greenimg = ImageTk.PhotoImage(ImageOps.expand(Image.open("Assets/green.png").resize((boardside//39,boardside//39),Image.ANTIALIAS)))
blueimg = ImageTk.PhotoImage(ImageOps.expand(Image.open("Assets/blue.png").resize((boardside//39,boardside//39),Image.ANTIALIAS)))
yellowimg = ImageTk.PhotoImage(ImageOps.expand(Image.open("Assets/yellow.png").resize((boardside//39,boardside//39),Image.ANTIALIAS)))

red = tk.Button(boardframe, image = redimg,border=0,highlightthickness=0,command= lambda: playerpop("Player 1"))
red.place(x=boardside-1.2*propwidth,y=boardside-0.75*propwidth,anchor='center')

green = tk.Button(boardframe, image = greenimg,border=0,highlightthickness=0,command= lambda: playerpop("Player 2"))
green.place(x=boardside-0.85*propwidth,y=boardside-0.75*propwidth,anchor='center')

blue = tk.Button(boardframe, image = blueimg,border=0,highlightthickness=0,command= lambda: playerpop("Player 3"))
blue.place(x=boardside-1.2*propwidth,y=boardside-0.4*propwidth,anchor='center')

yellow = tk.Button(boardframe, image = yellowimg,border=0,highlightthickness=0,command= lambda: playerpop("Player 4"))
yellow.place(x=boardside-0.85*propwidth,y=boardside-0.4*propwidth,anchor='center')

playerpopup = None
#endregion

dictionary = {0:["player1",red,0],1:["player2",green,0],2:["player3",blue,0],3:["player4",yellow,0]}
check,player = 0,[]
injail = False
def rolldice():
    global check,player
    player = dictionary[check%4]
    mixer.music.load("Assets/diceroll.mp3")
    mixer.music.play(loops=0)
    diceroll = random.randint(1,6),random.randint(1,6)
    for i in range(18):
        die1.configure(image=diedict[random.randint(1,6)])
        die2.configure(image=diedict[random.randint(1,6)])
        die1.update()
        die2.update()
        sleep(0.12)
    die1.configure(image=diedict[diceroll[0]])
    die2.configure(image=diedict[diceroll[1]])
    currmove = sum(diceroll)
    move(currmove)
    check+=1
#'check' variable for moving token turn by turn for now because checking
def move(move):
    x,y=float(player[1].place_info()['x']),float(player[1].place_info()['y'])
    for i in range(1,move+1):
        player[2]+=1
        posi = player[2]%40
        if player[1] is red:
            if posi in range(1,10):
                x-=propwidth
            elif posi==10:
                if injail:
                    x-=1.2*propwidth
                    y-= 0.4*propwidth
                else:
                    x-=1.75*propwidth
            elif posi==11:
                x+=0.6*propwidth
                y-=1.5*propwidth
            elif posi in range(12,20):
                y-=propwidth
            elif posi==20:
                x+=0.4*propwidth
                y-=1.1*propwidth
            elif posi in range(21,30):
                x+=propwidth
            elif posi == 30:
                x+=1.2*propwidth
                y+=0.4*propwidth
            elif posi in range(31,40):
                y+=propwidth
            else:
                x=boardside-1.2*propwidth
                y=boardside-0.75*propwidth
        elif player[1] is green:
            if posi in range(1,10):
                x-=propwidth
            elif posi==10:
                if injail:
                    x-=1.2*propwidth
                    y-= 0.4*propwidth
                else:
                    x-=2.1*propwidth
                    y-=0.4*propwidth
            elif posi==11:
                x+=0.6*propwidth
                y-=0.75*propwidth
            elif posi in range(12,20):
                y-=propwidth
            elif posi==20:
                x+=0.05*propwidth
                y-=1.45*propwidth
            elif posi in range(21,30):
                x+=propwidth
            elif posi == 30:
                x+=1.55*propwidth
                y+=0.07*propwidth
            elif posi in range(31,40):
                y+=propwidth
            else:
                x=boardside-0.85*propwidth
                y=boardside-0.75*propwidth
        elif player[1] is blue:
            if posi in range(1,10):
                x-=propwidth
            elif posi==10:
                if injail:
                    x-=1.2*propwidth
                    y-= 0.4*propwidth
                else:
                    x-=1.3*propwidth
                    y+=0.2*propwidth
            elif posi==11:
                x-=0.2*propwidth
                y-=2.05*propwidth
            elif posi in range(12,20):
                y-=propwidth
            elif posi==20:
                x+=0.74*propwidth
                y-=1.44*propwidth
            elif posi in range(21,30):
                x+=propwidth
            elif posi == 30:
                x+=1.53*propwidth
                y+=0.75*propwidth
            elif posi in range(31,40):
                y+=propwidth
            else:
                x=boardside-1.2*propwidth
                y=boardside-0.4*propwidth
        elif player[1] is yellow:
            if posi in range(1,10):
                x-=propwidth
            elif posi==10:
                if injail:
                    x-=1.2*propwidth
                    y-= 0.4*propwidth
                else:
                    x-=1.2*propwidth
                    y+=0.2*propwidth
            elif posi==11:
                x-=0.65*propwidth
                y-=1.7*propwidth
            elif posi in range(12,20):
                y-=propwidth
            elif posi==20:
                x+=0.4*propwidth
                y-=1.8*propwidth
            elif posi in range(21,30):
                x+=propwidth
            elif posi == 30:
                x+=1.87*propwidth
                y+=0.43*propwidth
            elif posi in range(31,40):
                y+=propwidth
            else:
                x=boardside-0.85*propwidth
                y=boardside-0.4*propwidth

        player[1].place(x=x,y=y)
        player[1].update()
        sleep(0.2)
    

roll = ttk.Button(boardframe, text="Roll Dice",style="my.TButton",command=rolldice)
roll.place(relx=0.5 ,rely=0.5,anchor='center')

die1 = tk.Label(boardframe,image=dice5,border=0,highlightthickness=0)
die1.place(relx=0.485,rely=0.46,anchor='se')

die2 = tk.Label(boardframe,image=dice5,border=0,highlightthickness=0)
die2.place(relx=0.515,rely=0.46,anchor='sw')


mainwin.bind('<Unmap>', minimize)
mainwin.bind('<Map>', maximize)
mainwin.mainloop()