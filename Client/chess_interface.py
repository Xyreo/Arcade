"""Multiplayer Chess Interface
Handles the multiplayer part of chess."""
import threading


class ServerInterface:
    def __init__(self, room) -> None:
        msg = ("CHESS", "START", "WHITE")
        room.broadcast_to_self(room.host, msg)
        for i in room.members:
            if i != room.host:
                msg = ("CHESS", "START", "BLACK")
                room.broadcast_to_self(i, msg)
        self.room = room

    def move(self, instruction, uuid):
        msg = ("CHESS", "MOVE", instruction[1])
        self.room.broadcast_to_members(uuid, msg)

    def update(self, uuid, instruction):
        self.move(instruction, uuid)


class ClientInterface:
    def __init__(self, updater) -> None:
        self.send = updater

    def played(self, move):
        self.send(("CHESS", "MOVE", move))
