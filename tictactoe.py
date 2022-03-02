import tkinter as tk
from tkinter import messagebox
from client_framework import *


        
    
def braindead(x):
    print(x)
    
root = tk.Tk()
root.title('TicTacToe')
root.resizable(False,False)

c = Client(('localhost',6789))
d = {'print': braindead,'cringe':12}
c.startrecv(d)
def click(b):
    pass

def send():
    s = inputtxt.get(1.0, "end-1c")
    if s == 'C':
        c.create_room()
    
    elif s == 'L':
        c.fetch_rooms()
        
    elif s == 'S':
        c.start()   
    
    elif s[0] == 'J':
        c.join_room(int(s[2:]))
        
b = []
for i in range(9):
    button = tk.Button(root,text = ' ', font = ('Helvetica',20),height = 2, width= 5, command = lambda a = i: click(b[a]))
    b.append(button)

for i in range(len(b)):
    b[i].grid(row = i%3, column = i//3)
    
submit = tk.Button(root,text = ':D', font = ('Helvetica',20),height = 2, width= 5, command = lambda a = i: send())
inputtxt = tk.Text(root,
                   height = 5,
                   width = 20)

inputtxt.grid(row=3, column=0,columnspan=3,sticky=tk.E + tk.W)
submit.grid()

  
    
root.mainloop()