import pickle
import socket
import threading
import sounddevice as sd
import sys

CHUNK = 1024
CHANNELS = 2
RATE = 44100

MAX_BYTES = 1024
HEADER_LEN = 1024


class Client:
    # Class that creates the client object for handling communications from the client's end
    # Implemented seperately to abstract the communications part from the game logic
    def __init__(self, ADDRESS, room):
        # Takes the address and connects to the server. Also strats a thread to handle listening
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect(ADDRESS)
        self.send(pickle.dumps(room))

        self.isTransmit = True
        self.isReceive = True

        self.sdstream = sd.Stream(samplerate=RATE, channels=CHANNELS, dtype="float32")
        self.sdstream.start()

        self.mic_thread = threading.Thread(target=self.mic, daemon=True)
        self.mic_thread.start()
        self.out_thread = threading.Thread(target=self.play, daemon=True)
        self.out_thread.start()
        while True:
            a = input()
            if a == "N":
                self.isTransmit = False
                self.isReceive = False
                break
        print("Over")

    def send(self, msg):
        data_len = len(msg)
        header = str(data_len).encode("utf-8")
        header_builder = b"0" * (HEADER_LEN - len(header)) + header
        self.conn.send(header_builder)
        for i in range(data_len // MAX_BYTES):
            self.conn.send(msg[i * MAX_BYTES : (i + 1) * MAX_BYTES])
        if data_len % MAX_BYTES != 0:
            self.conn.send(msg[-(data_len % MAX_BYTES) :])

    def close(self):
        self.connected = False
        self.conn.close()

    def play(self):
        while self.isReceive:
            try:
                dat = b""
                header = self.conn.recv(HEADER_LEN)
                data_len = int((header).decode("utf-8"))

                for i in range(data_len // MAX_BYTES):
                    dat += self.conn.recv(MAX_BYTES)
                if data_len % MAX_BYTES != 0:
                    dat += self.conn.recv(data_len % MAX_BYTES)

                instruction = pickle.loads(dat)
                self.sdstream.write(instruction[1])
            except Exception as e:
                print("Listen Error: " + str(e))
                break
        print("Listen Ended")

    def mic(self):
        while self.isTransmit:
            try:
                data = self.sdstream.read(CHUNK)
                self.send(pickle.dumps(data[0]))

            except Exception as e:
                print("Mic Error: " + str(e))
                break
        print("Mic Ended")


if __name__ == "__main__":
    Client(("localhost", 6969), 1)
