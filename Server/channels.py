# region Setup
from authenticator import Auth
import pickle, random, threading, secrets
import socket, ssl
from ssl import SSLContext

# endregion

lobbies = {}
rooms = {}
players = {}  # Stores the socks of all the players connected to the server


def assign_uuid(l):
    # Function that returns a unique id for passed object
    i = secrets.token_hex(16)
    while i in l:
        i = secrets.token_hex(16)
    return i


class Channels:
    def __init__(self, uuid):
        self.uuid = uuid
        self.members: list[Client] = []

    def broadcast_to_members(self, msg, exclude=None):
        for member in self.members:
            if member.uuid != exclude:
                member.send_instruction(msg)

    def join(self, player):
        self.members.append(player)
        player.channels.append(self.uuid)

    def leave(self, player):
        player.channels.remove(self.uuid)
        self.members.remove(players[player.uuid])


class Lobby(Channels):
    def __init__(self, uuid):
        super().__init__(uuid)
        lobbies[uuid] = self
        self.rooms: list[Room] = []
        self.game = uuid

    def create_room(self, host, settings):
        room = Room(host, settings, self.uuid)
        self.rooms.append(room)
        self.broadcast_to_members(
            ("ROOM", "ADD", room.details()), exclude=host.uuid
        )  # TODO Broadcast Protocol
        host.send_instruction(("ROOM", self.game, room.details()))

    def delete_room(self, id):
        rooms[id].delete()
        self.rooms.remove(rooms[id])
        del rooms[id]
        self.broadcast_to_members(("ROOM", "REMOVE", id))

    def join_room(self, player, id):
        rooms[id].join(player)

    def join(self, player):
        super().join(player)
        player.send_instruction((self.game, "INIT", self.details()))

    def broadcast_to_members(self, msg, exclude=None):
        super().broadcast_to_members((self.uuid,) + msg, exclude)

    def details(self):
        lobby = [room.details() for room in self.rooms if room.status == "OPEN"]
        return lobby


class Room(Channels):
    def __init__(self, host, settings, game, status="OPEN"):
        super().__init__(assign_uuid(rooms))
        rooms[self.uuid] = self
        self.host: Client = host
        self.settings = settings
        self.status = status
        self.game = game
        self.members.append(host)

    def delete(self):
        pass

    def start(self, player):
        if self.host.uuid != player.uuid:
            return
        self.status = "INGAME"
        if self.game == "CHESS":
            self.chess_start()
        elif self.game == "MNPLY":
            self.mnply_start()

    def join(self, player):
        super().join(player)
        self.broadcast(("PLAYER", "ADD", player.details()), self.uuid)
        player.send_instruction(("ROOM", self.game, self.details()))

    def leave(self, player):
        super().leave(player)
        if self.status == "OPEN" or self.status == "PRIVATE":
            self.broadcast(("PLAYER", "REMOVE", player.uuid))
        elif self.status == "INGAME":
            self.broadcast(("PLAYER", "LEAVE", player.uuid))

    def chess_start(self):
        pass

    def mnply_start(self):
        pass

    def broadcast(self, msg, exclude=None):
        self.broadcast_to_members(msg, exclude)
        lobbies[self.game].broadcast_to_members(msg + (self.uuid,))

    def broadcast_to_members(self, msg, exclude=None):
        super().broadcast_to_members((self.uuid,) + msg, exclude)

    def details(self):
        room = {
            "id": self.uuid,
            "host": self.host.uuid,
            "settings": self.settings,
            "members": [member.details() for member in self.members],
        }
        return room


PORT = 6789
SERVER = "0.0.0.0"  # TODO Option for local host/server
ADDRESS = (SERVER, PORT)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDRESS)


class Client(threading.Thread):
    # Class that gets threaded for every new client object
    # Handles all communication from client to servers

    def __init__(self, conn, addr, auth=True):
        # Object creation with conn -> socket, addr -> player ip address

        threading.Thread.__init__(self)
        self.conn = conn
        self.addr = addr
        self.auth = auth
        self.name = pickle.loads(self.conn.recv(1048))
        print("Name", self.name)
        self.uuid = assign_uuid(list(players.keys()))
        players[self.uuid] = self

        self.connected = True
        self.channels = []
        self.send_instruction(("NAME", self.uuid))

    def run(self):
        try:
            while self.connected:
                sent = self.conn.recv(1048)
                m = pickle.loads(sent)
                print("Received", m)
                t = threading.Thread(
                    target=self.authneticate,
                    args=(m,),
                    kwargs={"auth": self.auth},
                )
                t.start()
        except (EOFError, ConnectionResetError):
            self.close()
            self.conn.close()
            print("Connection Closed")
            return

    def authneticate(self, message, auth=False):
        if auth:
            if Driver.auth(message[0]):
                self.instruction_handler(message[1:])
            else:
                pass  # TODO unverified packet things
        else:
            self.instruction_handler(message)

    def instruction_handler(self, instruction):
        channel = instruction[0]
        print("Recv:", instruction)
        if channel == "0":
            self.main_handler(instruction[1:])
        elif channel in lobbies:
            self.lobby_handler(channel, instruction[1:])
        elif channel in rooms:
            self.room_handler(channel, instruction[1:])
        else:
            pass  # TODO Wrong Channel Stuff

    def main_handler(self, msg):
        action = msg[0]
        if action == "JOIN":
            lobbies[msg[1]].join(self)
        elif action == "LEAVE":
            lobbies[msg[1]].leave(self)
        else:
            pass  # TODO Wrong Action

    def lobby_handler(self, lobby, msg):
        action = msg[0]
        if action == "JOIN":
            lobbies[lobby].join_room(self, msg[1])
        elif action == "CREATE":
            lobbies[lobby].create_room(self, msg[1])
        elif action == "DELETE":
            lobbies[lobby].delete_room(msg[1])
        else:
            pass  # TODO Wrong Action

    def room_handler(self, room, msg):
        action = msg[0]
        if action == "START":
            rooms[room].start(self)
        elif action == "LEAVE":
            rooms[room].leave(self)
        elif action == "MSG":
            rooms[room].broadcast_to_members(msg[1:], self.uuid)

    def send_instruction(self, instruction):
        self.conn.send(pickle.dumps(instruction))
        print(instruction, "SENT.")

    def details(self):
        d = {"name": self.name, "puid": self.uuid}
        return d

    def close(self):
        for i in self.channels:
            if i in lobbies:
                lobbies[i].leave(self)
            elif i in rooms:
                rooms[i].leave(self)

        del players[self.uuid]


class Driver:
    auth: Auth = Auth()

    def __init__(self):
        PORT = 6778
        SERVER = "localhost"
        ADDRESS = (SERVER, PORT)

        l, c = Lobby("MNPLY"), Lobby("CHESS")
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        """sslcontext = SSLContext(ssl.PROTOCOL_TLS_SERVER)
        sslcontext.load_cert_chain("certificate.pem", keyfile="key.pem")
        self.server = sslcontext.wrap_socket(sock=self.server, server_side=True)"""
        self.server.bind(ADDRESS)

    def start(self):
        print("Server Started")
        self.server.listen()
        while True:
            conn, addr = self.server.accept()
            print(f"active connections {threading.active_count()-1}")
            client_thread = Client(conn, addr, False)
            client_thread.start()


players: dict[str, Client]
lobbies: dict[str, Lobby]
rooms: dict[str, Room]


if __name__ == "__main__":
    d = Driver()
    d.start()
