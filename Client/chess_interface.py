"""Multiplayer Chess Interface
Handles the multiplayer part of chess."""


from multiplayer_chess import Chess
import threading


class ServerInterface:
    def __init__(self) -> None:
        pass

    def serverside(instruction, room, uuid):
        if instruction[0] == "START":
            msg = ("CHESS", "START", instruction[1])
            room.broadcast_to_self(uuid, msg)
            color = "WHITE" if instruction[1] == "BLACK" else "BLACK"
            msg = ("CHESS", "START", color)
        else:
            msg = ("CHESS", "MOVE", instruction[1])

        room.broadcast_to_members(uuid, msg)


class ClientInterface:
    def __init__(self) -> None:
        pass

    def clientside(self, instruction, update):
        if instruction[0] == "START":
            t = threading.Thread(target=self.start_chess, args=(instruction[2], update))
            t.start()

    def start_chess(color):
        app = Chess(color)
        app.mainloop()
