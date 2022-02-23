import socket, threading, time, pickle
import tkinter as tk
from tkinter import ttk

PORT = 6789
SERVER = 'localhost' #TODO Option for local host/server
ADDRESS = (SERVER, PORT)
FORMAT = "utf-8"

server = socket.socket(socket.AF_INET,
					socket.SOCK_STREAM)
server.bind(ADDRESS)

players = []            #Stores the socks of all the players connected to the server
p_in_queue = []         #Stores player socks listening for room updations (they are waiting to join rooms)
rooms = []              #List to store all existing room objects

#region GUI             #Maybe changed later
root = tk.Tk()
width = root.winfo_screenwidth() - 800
height = root.winfo_screenheight() - 350
root.geometry("%dx%d%+d%+d" % (width, height, 100, 100))

columns = ('room_no', 'host_name', 'nply')
tree = ttk.Treeview(root, columns=columns, height=height, padding=5)
tree.column('#0', width=10)
tree.heading('#0', text = '')
tree.heading('room_no', text='Room No.')
tree.heading('host_name', text='Host Name')
tree.heading('nply', text='Number of Players')

tree.grid(row=0, column=0, sticky='nsew')
scrollbar = ttk.Scrollbar(root, orient=tk.VERTICAL, command=tree.yview)
tree.configure(yscroll=scrollbar.set)
scrollbar.grid(row=0, column=1, sticky='ns')
#endregion

class Room():
    #Class that stores Room objects to make functioning in rooms smoothly
    def __init__(self,host):
        self.players = []
        self.host = host
        self.satus = 'OPEN'
        
    def add(self, ply):
        self.players.append(ply)
        
    def details(self):
        d = {'Host'} #Room no, no of players, host
        return d

class Threaded_Client(threading.Thread):
    #Class that gets threaded for every new client object
    #Handles all communication from client to servers
    
    def __init__(self,conn,addr,name):
        #Object creation with conn -> socket, addr -> player ip address
        #TODO uuid
        
        threading.Thread.__init__(self)
        global players
        
        players.append(conn)
        self.conn = conn
        self.addr = addr
        self.name = name
        self.room = None
        
    def run(self):
        #Function called when <thread>.start() is called
        #So far just used to redirect user to create/join room
        
        self.todo = self.conn.recv(1024)
        if 'create' == pickle.loads(self.todo):
            self.create_room()
            
        elif 'join' == pickle.loads(self.todo):
            self.join_room()
            
    def join_room(self):
        #Function to redirect users to the joining page
        #TODO Client Instruction
        
        global p_in_queue, rooms
        p_in_queue.append(self.conn)
           
    def create_room(self):
        #Function to create a room
        #TODO send instruction to host client that room is created
        #TODO may implement more customizability (eg. Start Money, No. of Players etc.)
        
        global rooms, p_in_queue
        self.room = Room(self.addr) #TODO use name if decided upon
        rooms.append(self.room)
        self.conn.send(pickle.dumps(('ROOM','ACK')))
        
        #Informs all clients in lobby a new room has been created
        #TODO Everything
        
        for client in p_in_queue:
            if client.addr != self.addr(): #TODO uuid pls
                client.send(pickle.dumps(('ROOM','UPDATE'))) #TODO The room object ig ?
            
    def instruction_handler():
        pass
        
def start_server():
    #Function that listens for incoming connections and threads and redirects them to the Client Handler
    
    while True:
        conn, addr = server.accept()         
        client_thread = Threaded_Client(conn,addr)
        client_thread.start()

        print(f"active connections {threading.activeCount()-2}")

#Threads the server itself to manage the GUI of the server seperately
svr = threading.Thread(target = start_server)
svr.start()

root.mainloop()