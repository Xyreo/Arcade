import threading, socket, pickle

class Client():
    #Class that creates the client object for handling communications from the client's end
    #Implemented seperately to abstract the communications part from the game logic 
    
    def __init__(self,ADDRESS):
        #Takes the address and connects to the server. Also strats a thread to handle listening
        #TODO Might need more info for customizability
        
        self.conn = socket.socket(socket.AF_INET,
					socket.SOCK_STREAM)
        
        self.conn.connect(ADDRESS)
        self.connected = True
        self.uuid = None
        
        
        
    def create_room(self):
        pass
    
    def join_room(self):
        pass
    
    def startrecv(self):
        listening_thread = threading.Thread(target=self.listener)
        listening_thread.start()
    
    def listener(self):
        while self.connected:
            instruction = self.conn.recv(1024)
            instruction = pickle.loads(instruction)
            