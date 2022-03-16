def serverside(instruction, room, uuid):
    if instruction[0] == "START":
        msg = ("CHESS", "START", instruction[1])
        room.broadcast_to_self(uuid, msg)
        color = "WHITE" if instruction[1] == "BLACK" else "BLACK"
        msg = ("CHESS", "START", color)
    else:
        msg = ("CHESS", "MOVE", instruction[1])

    room.broadcast_to_members(uuid, msg)
