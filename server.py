import socket, threading, time, pickle, random
import tkinter as tk
from tkinter import ttk

PORT = 6789
SERVER = 'localhost' #TODO Option for local host/server
ADDRESS = (SERVER, PORT)
FORMAT = "utf-8"

server = socket.socket(socket.AF_INET,
					socket.SOCK_STREAM)
server.bind(ADDRESS)

players = {}            #Stores the socks of all the players connected to the server
p_in_queue = []         #Stores player socks listening for room updations (they are waiting to join rooms)
rooms = {}              #Dicitonary to store all existing room objects

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
        self.members = []
        self.host = host
        self.satus = 'OPEN'
        self.uuid = assign_uuid(list(rooms.keys()))
        rooms[self.uuid] = self
        
    def add(self, piid):
        self.members.append(piid)
        
    def details(self):
        #Function to return a dictionary containing details of the room
        
        d = {'host':players[self.host].name,  
             'numply':len(self.members),
             'roomnum':self.uuid}
        
        return d
    
    def start(self):
        self.status = 'INGAME'
        for i in self.members:
            players[i].send_instruction(pickle.dumps('ROOM','START'))

class Client(threading.Thread):
    #Class that gets threaded for every new client object
    #Handles all communication from client to servers
    
    def __init__(self,conn,addr,name):
        #Object creation with conn -> socket, addr -> player ip address
        
        threading.Thread.__init__(self)
        global players
            
        self.conn = conn
        self.addr = addr
        self.name = name
        self.room = None
        self.uuid = assign_uuid(list[players.keys()])
        self.connected = True
        
        players[self.uuid] = self
        
    def run(self):
        #Event Listener
        
        while self.connected:
            sent = self.conn.recv(1048)
            self.instruction_handler(pickle.loads(sent))
                       
    def join_room(self,mode):
        #Function to redirect users to the joining page
        
        if mode[0] == 'LIST':
            global p_in_queue, rooms
            p_in_queue.append(self)
            room_list = []
            for i in rooms.values():
                if i.status == 'OPEN':
                    room_list.append(i.details()) 
            
            package = ('ROOM','ADD', room_list)                  
            self.conn.send(pickle.dumps(package))
            
        else:
            self.room = rooms[mode[0]]
            self.room.add(self.uiid)
           
    def create_room(self):
        #Function to create a room
        #TODO may implement more customizability (eg. Start Money, No. of Players etc.)
        
        global p_in_queue
        self.room = Room(self.uuid)
        #Informs all clients in lobby a new room has been created        
        for client in p_in_queue: 
            i = ('ROOM','ADD',[self.room.details()])
            client.send_instruction(pickle.dumps(i))

    def instruction_handler(self,instruction):
        #Parses the request and redirects it appropriately
        
        if instruction[0] == 'ROOM':
            
            if instruction[1] == 'JOIN':
                self.join_room(instruction[2:])
            
            elif instruction[1] == 'CREATE':
                self.create_room()
            
            elif instruction[1] == 'START':
                self.room.start()
        
    def send_instruction(self, instruction):
        self.conn.send(instruction)
        
def assign_uuid(l):
    #Function that returns a unique id for passed object
    
    i = random.randint(1000,9999)
    while i in l:
        i = random.randint(1000,9999)
    return i
        
def start_server():
    #Function that listens for incoming connections and threads and redirects them to the Client Handler
    
    while True:
        conn, addr = server.accept()         
        client_thread = Client(conn,addr)
        client_thread.start()

        print(f"active connections {threading.activeCount()-2}")

#Threads the server itself to manage the GUI of the server seperately
svr = threading.Thread(target = start_server)
svr.start()

root.mainloop()