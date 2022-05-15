import pickle
import socket
from ssl import SSLContext, CERT_REQUIRED
import threading
import ssl


class Client:
    # Class that creates the client object for handling communications from the client's end
    # Implemented seperately to abstract the communications part from the game logic

    def __init__(self, ADDRESS, updater):
        # Takes the address and connects to the server. Also strats a thread to handle listening

        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        """sslcontext = SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        sslcontext.check_hostname = False
        sslcontext = ssl.create_default_context()
        sslcontext.check_hostname = False
        self.conn = sslcontext.wrap_socket(self.conn, server_hostname="Arcade")"""

        self.conn.connect(ADDRESS)
        print("Connected")
        self.connected = True
        self.uuid = None
        self.updater = updater
        self.listening_thread = threading.Thread(target=self.listener)
        self.listening_thread.start()

    def send(self, msg):
        self.conn.send(pickle.dumps(msg))

    def listener(self):
        while self.connected:
            instruction = self.conn.recv(1024)
            instruction = pickle.loads(instruction)
            self.updater(instruction)
