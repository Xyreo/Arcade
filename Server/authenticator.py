def generate_id():
    id = ""
    for i in range(16):
        id += chr(random.randint(33, 125))
    return id


def create_session(uuid):
    while True:
        session_id = generate_id()
        query = f"SELECT COUNT(*) FROM session_id WHERE session_id='{session_id}'"
        cursor.execute(query)


def check_session(uuid):
    pass


def end_session(uuid):
    pass
