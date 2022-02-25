def serverside(instruction):
    msg = ('MONOPOLY',)
    #TODO If decided on server handles rolling, then add that
    uuid = instruction[0]
    if instruction[1] == 'ROLLDICE':
        msg += instruction[1:]
        
    elif instruction[1] == 'BUILD':
        pass
    
    return msg 

def clientside():
    pass