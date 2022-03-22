"""Multiplayer Chess Interface
Handles the multiplayer part of chess."""
import threading


class ServerInterface:
    def __init__(self, room) -> None:
        msg = ("CHESS", "START", "WHITE")
        room.broadcast_to_self(room.host, msg)
        msg = ("CHESS", "START", "BLACK")
        room.broadcast_to_members(room.host, msg)
        self.room = room

    def move(self, instruction, uuid):
        msg = ("CHESS", "MOVE", instruction[1])
        self.room.broadcast_to_members(uuid, msg)

    def update(self, uuid, instruction):
        self.move(instruction, uuid)


class ClientInterface:
    def __init__(self, updater, game, color) -> None:
        self.send = updater
        t = threading.Thread(target=self.start_chess, args=(color, game))
        t.start()

    def start_chess(self, color, game):
        print("Eg")
        self.app = game(color, self.played)
        self.app.mainloop()

    def move(self, instruction):
        self.app.move(sent=instruction, multi=True)

    def played(self, move):
        self.send("CHESS", "MOVE", move)
