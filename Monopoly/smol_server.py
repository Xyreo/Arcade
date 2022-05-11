# region Setup
import pickle, random, threading, secrets
import socket, ssl
from ssl import SSLContext
from multipledispatch import dispatch

# endregion

players = {}  # Stores the socks of all the players connected to the server


def assign_uuid(l):
    # Function that returns a unique id for passed object
    i = secrets.token_hex(16)
    while i in l:
        i = secrets.token_hex(16)
    return i


PORT = 6789
SERVER = "0.0.0.0"  # TODO Option for local host/server
ADDRESS = (SERVER, PORT)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDRESS)


class Client(threading.Thread):
    # Class that gets threaded for every new client object
    # Handles all communication from client to servers

    color = ["Red", "Green", "Blue", "Gold"]

    def __init__(self, conn, addr, name):
        # Object creation with conn -> socket, addr -> player ip address

        threading.Thread.__init__(self)
        self.conn = conn
        self.addr = addr
        self.name = name
        self.uuid = assign_uuid(list(players.keys()))
        players[self.uuid] = self

        self.connected = True

    def run(self):
        try:
            while self.connected:
                sent = self.conn.recv(1048)
                m = pickle.loads(sent)
                print("Received", m)
                self.instruction_handler(m)

        except KeyboardInterrupt as e:
            server.close()

    def instruction_handler(self, msg):
        action = msg[0]
        if action == "START":
            p = {}
            for i in range(len(players)):
                p[players.uuid] = {"Name": players[i].name, "Colour": Client.color[i]}
            for player in players:
                player.send(("START", p, self.uuid))

        elif action in ["ROLL", "BUY", "RENT", "TAX", "MORTGAGE", "ENDTURN"]:
            self.broadcast_to_members((self.uuid,) + msg, self.uuid)

    def broadcast_to_members(self, msg, exclude=None):
        for player in players:
            if player.uuid != exclude:
                player.send_instruction(msg)

    def send_instruction(self, instruction):
        self.conn.send(pickle.dumps(instruction))
        print(instruction, "SENT.")


class Driver:
    def __init__(self):
        PORT = 6666
        SERVER = "localhost"
        ADDRESS = (SERVER, PORT)
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(ADDRESS)

    def start(self):
        print("Server Started")
        self.server.listen()
        while True:
            conn, addr = self.server.accept()
            print("Accepted from", addr)
            client_thread = Client(conn, addr, False)
            client_thread.start()
            print(f"active connections {threading.activeCount()-2}")


if __name__ == "__main__":
    d = Driver()
    d.start()
