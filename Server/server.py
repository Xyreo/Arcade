# region Setup
import pickle
import random
import socket
import ssl
import threading

import chess_interface

PORT = 6789
SERVER = "0.0.0.0"
ADDRESS = (SERVER, PORT)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server = ssl.wrap_socket(
    server, server_side=True, keyfile="./key.pem", certfile="./certificate.pem"
)
server.bind(ADDRESS)

players = {}  # Stores the socks of all the players connected to the server
p_in_queue = []  # Stores players in lobby
rooms: dict = {}  # Dicitonary to store all existing room objects


class Room:
    # Class that stores Room objects to make functioning in rooms smoothly
    def __init__(self, host: int, type: str):
        self.members: list[Client] = [host]
        self.host: int = host
        self.status = "OPEN"
        self.uuid = assign_uuid(list(rooms.keys()))
        self.type = type
        rooms[self.uuid] = self
        msg = ("ROOM", "ADDROOM", [players[host].details()])
        self.broadcast_to_self(host, msg)
        print(
            f"Room Created: {self.uuid}\nHost: {players[host].name}\nGame: {self.type}\n"
        )

        # Informs all clients in lobby a new room has been created
        for client in p_in_queue:
            i = ("ROOM", "ADD", [self.details()])
            client.send_instruction(i)

    def add_player(self, puid):
        self.members.append(puid)

        msg = ("ROOM", "ADDROOM", [players[puid].details()])
        self.broadcast_to_members(puid, msg)

        msg = ("ROOM", "ADDROOM", [players[i].details() for i in self.members])
        self.broadcast_to_self(puid, msg)

        print(f"Player {players[puid].name} joined room {self.uuid}\n")

    def details(self):
        # Function to return a dictionary containing details of the room

        details = {
            "host": players[self.host].name,
            "players": [players[i].details() for i in self.members],
            "roomnum": self.uuid,
            "type": self.type,
        }

        return details

    def start(self):
        self.status = "INGAME"
        for i in self.members:
            p_in_queue.remove

        for i in p_in_queue:
            i.send_instruction(("ROOM", "REMOVE", self.uuid))

        if self.type == "CHESS":
            self.game_handler = chess_interface.ServerInterface(self)

    def broadcast_to_members(self, initiator, msg):
        for i in self.members:
            if i != initiator:
                print("Out:", players[i].name, msg)
                players[i].send_instruction(msg)

    def broadcast_to_self(self, initiator, msg):
        print("To self,", players[initiator].name, ":", msg)
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
        self.name: str = None
        self.room: Room = None
        self.uuid = assign_uuid(list(players.keys()))
        self.connected = True

        players[self.uuid] = self

    def run(self):
        # Event Listener

        while self.connected:
            sent = self.conn.recv(1048)
            m = pickle.loads(sent)
            self.instruction_handler(m)

    def join_room(self, ruid):
        # Function to redirect users to the joining page
        self.room: Room = rooms[ruid]
        self.room.add_player(self.uuid)
        p_in_queue.remove(self)

    def list_room(self):
        if self not in p_in_queue:
            p_in_queue.append(self)

        room_list = []
        for i in rooms.values():
            if i.status == "OPEN":
                room_list.append(i.details())

        package = ("ROOM", "ADD", room_list)
        self.send_instruction(package)

    def create_room(self, type):
        # Function to create a room
        # TODO may implement more customizability (eg. Start Money, No. of Players etc.)
        global p_in_queue

        self.room = Room(self.uuid, type)

    def instruction_handler(self, instruction):
        # Parses the request and redirects it appropriately
        print("Received:", self.name, instruction)
        if instruction[0] == "ROOM":
            if instruction[1] == "JOIN":
                self.join_room(instruction[2])

            elif instruction[1] == "CREATE":
                self.create_room(instruction[2])

            elif instruction[1] == "LIST":
                self.list_room()

            elif instruction[1] == "START":
                self.room.start()

        elif instruction[0] == "NAME":
            self.name = instruction[1]
            self.send_instruction(("NAME", self.uuid))
            print(f"Active connections : {threading.activeCount()-2}")
            print(f"Player {self.name} joined.\n")

        elif instruction[0] == "CHESS":
            self.room.game_handler.update(self.uuid, instruction[1:])

    def send_instruction(self, instruction):
        self.conn.send(pickle.dumps(instruction))

    def details(self):
        details = {"name": self.name, "puid": self.uuid}
        return details


def assign_uuid(l):
    # Function that returns a unique id for passed object

    i = random.randint(1000, 9999)
    while i in l:
        i = random.randint(1000, 9999)
    return i


def start_server():
    # Function that listens for incoming connections and threads and redirects them to the Client Handler
    print("Server started...")
    server.listen()
    print("Server is listening for connections...")
    while True:
        conn, addr = server.accept()
        client_thread = Client(conn, addr)
        client_thread.start()


# Threads the server itself to manage the GUI of the server seperately
svr = threading.Thread(target=start_server)
svr.start()
