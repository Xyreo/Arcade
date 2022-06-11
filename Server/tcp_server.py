import pickle
import random
import secrets
import socket
import threading

from authenticator import Auth

lobbies = {}
rooms = {}
players = {}  # Stores the socks of all the players connected to the server


def log(msg):
    with open("tcp_log.txt", "a") as f:
        f.write(msg + "\n")


def assign_uuid(l):
    # Function that returns a unique id for passed object
    i = secrets.token_hex(3)
    while i in l:
        i = secrets.token_hex(3)
    return i.upper()


class Channels:
    def __init__(self, uuid):
        self.uuid = uuid
        self.members = []

    def broadcast_to_members(self, msg, exclude=None):
        for member in self.members:
            if member.uuid != exclude:
                member.send_instruction(msg)

    def join(self, player):
        self.members.append(player)
        player.channels.append(self.uuid)

    def leave(self, player):
        player.channels.remove(self.uuid)
        self.members.remove(player)


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
    def __init__(self, host, settings, game):
        super().__init__(assign_uuid(rooms))
        rooms[self.uuid] = self
        self.host: Client = host
        self.settings = settings
        self.status = self.settings["INITAL_STATUS"]
        self.game = game
        super().join(host)
        host.send_instruction(("ROOM", self.game, self.details()))

    def delete(self):
        self.broadcast(("ROOM", "REMOVE"))
        lobbies[self.game].rooms.remove(self)
        del rooms[self.uuid]

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
        if self.status in ["OPEN", "PRIVATE"]:
            if player.uuid == self.host.uuid:
                self.delete()
            else:
                self.broadcast(("PLAYER", "REMOVE", player.uuid))

        elif self.status == "INGAME":
            self.broadcast(("PLAYER", "LEAVE", player.uuid))

        super().leave(player)

    def chess_start(self):
        for i in self.members:
            if i.uuid == self.host.uuid:
                i.send_instruction((self.uuid, "ROOM", "START", "WHITE"))
            else:
                i.send_instruction((self.uuid, "ROOM", "START", "BLACK"))

    def mnply_start(self):
        p = {}
        color = ["red", "green", "blue", "gold"]
        order = (None, None)
        order[0] = [i for i in range(20)]
        random.shuffle(order[0])
        i = 0
        for player in self.members:
            p[player.uuid] = {"Name": player.name, "Colour": color[i]}
            i += 1
        for player in self.members:
            player.send_instruction((self.uuid, "ROOM", "START", (p, player.uuid)))

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

    def msg(self, m, ex):
        if self.game == "CHESS":
            self.broadcast_to_members(m, ex)
        elif self.game == "MNPLY":
            a, b = m
            m = (a, (ex,) + b)
            self.broadcast_to_members(m, ex)


class Client(threading.Thread):
    # Class that gets threaded for every new client object
    # Handles all communication from client to servers

    def __init__(self, conn, addr, auth=True):
        # Object creation with conn -> socket, addr -> player ip address

        threading.Thread.__init__(self)
        self.conn = conn
        self.addr = addr
        self.auth = auth
        try:
            self.name = pickle.loads(self.conn.recv(1048))
        except:
            print("AAAA")
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
                    target=self.authenticate,
                    args=(m,),
                    kwargs={"auth": self.auth},
                )
                t.start()
        except (EOFError, ConnectionResetError):
            self.close()
            self.conn.close()
            print("Connection Closed")
            return
        except Exception as e:
            log(f"Load Error: {e}")

    def authenticate(self, message, auth=False):
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
            rooms[room].msg(("MSG", msg[1]), self.uuid)

    def send_instruction(self, instruction):
        try:
            self.conn.send(pickle.dumps(instruction))
            print(instruction, "SENT.")
        except (ConnectionResetError, EOFError, BrokenPipeError):
            print("Couldnt send the message-", instruction)
        except Exception as e:
            log(f"Sending: {e}")

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
        PORT = 6969
        SERVER = "0.0.0.0"
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


if __name__ == "__main__":
    d = Driver()
    d.start()
