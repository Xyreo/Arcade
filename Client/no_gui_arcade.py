from chess import Chess
from client_framework import Client
from http_wrapper import Http
from monopoly import Monopoly
import json
import os
import threading
import time
import tkinter as tk

game = "MNPLY"
sent_time = time.perf_counter()
pid = None
rid = None
r = None
g = None
p = None


def send(*msg):
    global sent_time
    time_gap = 0.1
    new_time = time.perf_counter()
    if (sent_time + time_gap) > new_time:
        t = threading.Thread(
            target=queue_send,
            args=(msg, (sent_time + time_gap - new_time)),
        )
        t.start()
    else:
        queue_send(msg, None)


def queue_send(msg, t):
    global sent_time
    if t != None:
        sent_time = sent_time + 0.1
        time.sleep(t)
    else:
        sent_time = time.perf_counter() + 0.1
    print("Sent:", msg)
    c.send(msg)


def event_handler(msg):
    global p
    print("Recv:", msg)
    global pid, rid, r, game, g
    if msg[0] == "NAME":
        pid = msg[1]

    elif msg[0] == game:
        if msg[1] == "INIT":
            send("0", "LEAVE", game)
            if len(msg[2]) == 0:
                p = 1
                send(game, "CREATE", {"INITAL_STATUS": "OPEN", "MAX_PLAYERS": 4})
            else:
                send(game, "JOIN", msg[2][0]["id"])
                p = 2
    elif msg[0] == "ROOM":
        r = msg[2]
        rid = msg[2]["id"]

    elif msg[0] == rid:
        if msg[1] == "PLAYER":
            if pid == r["host"] and msg[2] == "ADD":
                time.sleep(0.2)
                send(rid, "START")
        elif msg[1] == "ROOM":
            if msg[2] == "START":
                h = Http("http://167.71.231.52:5000")
                h.login("user" + str(p), "pass" + str(p))
                g = Monopoly(
                    msg[3][0], msg[3][1], lambda move: send(rid, "MSG", move), h
                )
                print("NANI")

        elif msg[1] == "MSG":
            g.opp_move(msg[2])


root = tk.Tk()
c = Client(("localhost", 6960), event_handler)
send("Gay")
send("0", "JOIN", game)
root.mainloop()
