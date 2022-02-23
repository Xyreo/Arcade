import socket, threading, time, pickle
import tkinter as tk
from tkinter import ttk

PORT = 6789
SERVER = ''
ADDRESS = (SERVER, PORT)
FORMAT = "utf-8"

server = socket.socket(socket.AF_INET,
					socket.SOCK_STREAM)
server.bind(ADDRESS)

players = {}
rooms = []

#region
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
    def __init__(self,host):
        self.players = []
        self.host = host
        
    def add(self, ply):
        self.players.append(ply)

class Threaded_Client(threading.Thread):
    def __init__(self,conn,addr):
        threading.Thread.__init__(self)
        self.conn = conn
        self.addr = addr
        self.room = None
        
    def run(self):
        self.todo = self.conn.recv(1024)
        if 'create' == pickle.loads(self.todo):
            self.create_room()
            
        elif 'join' == pickle.loads(self.todo):
            self.join_room()
            
    def join_room(self):
        pass
    
    def create_room(self):
        global rooms
        self.room = Room(self.addr)
        rooms.append(self.room)
    
def start_server():
    while True:
        global players
        conn, addr = server.accept()         
        client_thread = Threaded_Client(conn,addr)
        client_thread.start()

        print(f"active connections {threading.activeCount()-1}")

svr = threading.Thread(target = start_server)
svr.start()

root.mainloop()