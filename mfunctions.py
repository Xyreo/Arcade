def serverside(instruction):
    # TODO If decided on server handles rolling, then add that
    uuid = instruction[0]
    msg = ('MONOPOLY', uuid)
    if instruction[1] == 'ROLLDICE':
        msg += instruction[1:]

    elif instruction[1] == 'BUILD':
        pass

    return msg


def clientside(callbacks, initiator, instruction):
    if instruction[0] == 'ROLLDICE':
        callbacks['ROLLDICE'](initiator, instruction[1])

    elif instruction[0] == 'BUILD':
        pass
