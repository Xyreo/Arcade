import threading, socket, pickle


class Client:
    # Class that creates the client object for handling communications from the client's end
    # Implemented seperately to abstract the communications part from the game logic

    def __init__(self, ADDRESS):
        # Takes the address and connects to the server. Also strats a thread to handle listening

        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect(ADDRESS)
        self.connected = True
        self.uuid = None

    def startrecv(self, updater):
        t = (updater,)
        self.listening_thread = threading.Thread(target=self.listener, args=t)
        self.listening_thread.start()

    def send(self, msg):
        self.conn.send(pickle.dumps(msg))

    def listener(self, updater):
        while self.connected:
            instruction = self.conn.recv(1024)
            instruction = pickle.loads(instruction)
            updater(instruction)


class Chess:
    def __init__(self) -> None:
        pass
