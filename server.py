# region Setup
import socket
import threading
import pickle
import random
import mfunctions as mnply
import chessfunctions as chess

PORT = 8080
SERVER = "0.0.0.0"  # TODO Option for local host/server
ADDRESS = (SERVER, PORT)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDRESS)

players = {}  # Stores the socks of all the players connected to the server
# Stores player socks listening for room updations (they are waiting to join rooms)
p_in_queue = []
rooms = {}  # Dicitonary to store all existing room objects
# endregion

# region GUI             #Maybe changed later


class Room:
    # Class that stores Room objects to make functioning in rooms smoothly
    def __init__(self, host):
        self.members: list[Client] = [host]
        self.host: list = host
        self.status = "OPEN"
        self.uuid = assign_uuid(list(rooms.keys()))
        rooms[self.uuid] = self

    def add(self, puid):
        self.members.append(puid)
        msg = ("ROOM", "ADDROOM", players[puid].details())
        self.broadcast_to_members(puid, msg)

    def details(self):
        # Function to return a dictionary containing details of the room

        d = {
            "host": players[self.host].name,
            "players": [players[i].details() for i in self.members],
            "roomnum": self.uuid,
        }

        return d

    def start(self):
        self.status = "INGAME"
        for i in self.members:
            players[i].send_instruction(("ROOM", "START"))

        for i in p_in_queue:
            i.send_instruction(("ROOM", "REMOVE", self.uuid))

    def broadcast_to_members(self, initiator, msg):
        for i in self.members:
            if i != initiator:
                print("Out:", i, msg)
                players[i].send_instruction(msg)

    def broadcast_to_self(self, initiator, msg):
        players[initiator].send_instruction(msg)


class Client(threading.Thread):
    # Class that gets threaded for every new client object
    # Handles all communication from client to servers

    def __init__(self, conn, addr):
        # Object creation with conn -> socket, addr -> player ip address

        threading.Thread.__init__(self)
        global players

        self.conn = conn
        self.addr = addr
        self.name = None
        self.room = None
        self.uuid = assign_uuid(list(players.keys()))
        self.connected = True

        players[self.uuid] = self

    def run(self):
        # Event Listener

        while self.connected:
            sent = self.conn.recv(1048)
            m = pickle.loads(sent)
            self.instruction_handler(m)

    def join_room(self, mode):
        # Function to redirect users to the joining page
        global p_in_queue, rooms
        if mode == "LIST":
            if self not in p_in_queue:
                p_in_queue.append(self)

            room_list = []
            for i in rooms.values():
                if i.status == "OPEN":
                    room_list.append(i.details())

            package = ("ROOM", "ADD", room_list)
            self.send_instruction(package)

        else:
            self.room = rooms[mode]
            self.room.add(self.uuid)
            p_in_queue.remove(self)

    def create_room(self):
        # Function to create a room
        # TODO may implement more customizability (eg. Start Money, No. of Players etc.)
        global p_in_queue

        self.room = Room(self.uuid)
        # Informs all clients in lobby a new room has been created
        for client in p_in_queue:
            i = ("ROOM", "ADD", [self.room.details()])
            client.send_instruction(i)

    def instruction_handler(self, instruction):
        # Parses the request and redirects it appropriately
        print(instruction)
        if instruction[0] == "ROOM":
            if instruction[1] == "JOIN":
                self.join_room(instruction[2])

            elif instruction[1] == "CREATE":
                self.create_room()

            elif instruction[1] == "START":
                self.room.start()

        elif instruction[0] == "NAME":
            self.name = instruction[1]

        elif instruction[0] == "MONOPOLY":
            msg = mnply.serverside(instruction[1:])
            self.room.broadcast_to_members(self.uuid, msg)

        elif instruction[0] == "CHESS":
            chess.serverside(instruction[1:], self.room, self.uuid)

    def send_instruction(self, instruction):
        self.conn.send(pickle.dumps(instruction))
        print("SENT.")

    def details(self):
        d = {"name": self.name, "puid": self.uuid}
        return d


def assign_uuid(l):
    # Function that returns a unique id for passed object

    i = random.randint(1000, 9999)
    while i in l:
        i = random.randint(1000, 9999)
    return i


def start_server():
    # Function that listens for incoming connections and threads and redirects them to the Client Handler

    server.listen()
    while True:
        conn, addr = server.accept()
        client_thread = Client(conn, addr)
        client_thread.start()

        print(f"active connections {threading.activeCount()-2}")


# Threads the server itself to manage the GUI of the server seperately
svr = threading.Thread(target=start_server)
svr.start()
