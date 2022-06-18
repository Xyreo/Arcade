import datetime
import pickle
import random
import secrets
import socket
import threading

from authenticator import Auth

lobbies = {}
rooms = {}
players = {}  # Stores the socks of all the players connected to the server

l = [1, 2]
MAX_BYTES = 1024
HEADER_LEN = 1024


def log(*msg):
    # print(" ".join(map(str, msg)))
    with open("vc_log.txt", "a") as f:
        x = datetime.datetime.now()
        f.write(x.strftime("[%d/%m/%y %H:%M:%S] ") + " ".join(map(str, msg)) + "\n")


def assign_uuid(l):
    # Function that returns a unique id for passed object
    i = secrets.token_hex(3)
    while i in l:
        i = secrets.token_hex(3)
    return i.upper()


class Room:
    def __init__(self, uuid):
        self.uuid = uuid
        self.members = []
        rooms[self.uuid] = self

    def delete(self):
        if self.uuid in rooms:
            del rooms[self.uuid]

    def join(self, player):
        if player not in self.members:
            self.members.append(player)

    def leave(self, player):
        if player in self.members:
            self.members.remove(player)

        if len(self.members) == 0:
            log(f"{self.uuid} voice chat closed")
            self.delete()

    def broadcast_to_members(self, msg, exclude=None):
        for member in self.members:
            if member.uuid != exclude:
                member.send_instruction(msg)


class Client(threading.Thread):
    # Class that gets threaded for every new client object
    # Handles all communication from client to servers

    def __init__(self, conn, addr):
        # Object creation with conn -> socket, addr -> player ip address

        threading.Thread.__init__(self)
        self.conn = conn
        self.addr = addr
        self.room = pickle.loads(self.receive())
        self.room_join()
        log(f"Connected to {self.addr} for room {self.room}")

        self.uuid = assign_uuid(list(players.keys()))
        players[self.uuid] = self

    def room_join(self):
        if self.room not in rooms:
            Room(self.room)
        rooms[self.room].join(self)

    def receive(self):
        try:
            dat = b""
            header = self.conn.recv(HEADER_LEN)
            if not header:
                self.close()
                return
            data_len = int((header).decode("utf-8"))

            for i in range(data_len // MAX_BYTES):
                dat += self.conn.recv(MAX_BYTES)
            if data_len % MAX_BYTES != 0:
                dat += self.conn.recv(data_len % MAX_BYTES)
            log(1)
            return dat

        except (EOFError, ConnectionResetError):
            self.close()

    def run(self):
        while True:
            msg = self.receive()
            if not msg:
                break
            rooms[self.room].broadcast_to_members(
                pickle.dumps((self.uuid, pickle.loads(msg))), self.uuid
            )

    def send_instruction(self, msg):

        try:
            data_len = len(msg)
            header = str(data_len).encode("utf-8")
            header_builder = b"0" * (HEADER_LEN - len(header)) + header
            self.conn.send(header_builder)
            for i in range(data_len // MAX_BYTES):
                self.conn.send(msg[i * MAX_BYTES : (i + 1) * MAX_BYTES])
            if data_len % MAX_BYTES != 0:
                self.conn.send(msg[-(data_len % MAX_BYTES) :])

        except socket.error:
            log("Couldnt send the message-")
        except (ConnectionResetError, EOFError, BrokenPipeError):
            log("Couldnt send the message-")
        except Exception as e:
            log(f"Error Sending: {e}")

    def close(self):
        if self.room in rooms:
            rooms[self.room].leave(self)
        self.channels = []
        if self.uuid in players:
            del players[self.uuid]
        self.conn.close()
        log(
            f"Connection to {self.addr} closed. {threading.active_count() - 2} players connected"
        )


class Driver:
    auth: Auth = Auth()

    def __init__(self):
        PORT = 6969
        SERVER = "0.0.0.0"
        ADDRESS = (SERVER, PORT)
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        """sslcontext = SSLContext(ssl.PROTOCOL_TLS_SERVER)
        sslcontext.load_cert_chain("certificate.pem", keyfile="key.pem")
        self.server = sslcontext.wrap_socket(sock=self.server, server_side=True)"""
        self.server.bind(ADDRESS)

    def start(self):
        log("Server Started")
        self.server.listen()
        while True:
            conn, addr = self.server.accept()
            log(f"Active connections {threading.active_count()-1}")
            client_thread = Client(conn, addr)
            client_thread.start()


rooms: list[Room]


if __name__ == "__main__":
    d = Driver()
    d.start()
