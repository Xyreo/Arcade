import pickle
import socket
import threading


class Client:
    # Class that creates the client object for handling communications from the client's end
    # Implemented seperately to abstract the communications part from the game logic
    def __init__(self, ADDRESS, updater, authtoken=None):
        # Takes the address and connects to the server. Also strats a thread to handle listening
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.token = authtoken
        self.conn.connect(ADDRESS)
        print("Connected")
        self.connected = True
        self.uuid = None
        self.updater = updater
        self.listening_thread = threading.Thread(target=self.listener)
        self.listening_thread.start()

    def send(self, msg):
        self.conn.send(pickle.dumps((self.token,) + msg))

    def close(self):
        self.connected = False
        self.conn.close()

    def listener(self):
        while self.connected:
            try:
                instruction = self.conn.recv(1024)
                if not instruction:
                    print("Server Unexpectedly Quit")
                    break
                instruction = pickle.loads(instruction)
                self.updater(instruction)
            except OSError:
                pass
