import random, redis
from datetime import timedelta


class Auth:
    def __init__(self):
        self.r = redis.Redis(host="localhost", port=6379, db=1)

    @staticmethod
    def generate_id():
        id = ""
        for i in range(16):
            id += chr(random.randint(33, 125))
        return id

    def add(self, name):
        for i in self.r.keys():
            if name == self.r.get(i).decode("utf-8"):
                self.r.delete(i)

        session_id = Auth.generate_id()
        while self.r.exists(session_id):
            session_id = Auth.generate_id()
        self.r.setex(session_id, timedelta(minutes=30), value=name)
        return session_id

    def __call__(self, session_id):
        if self.r.exists(session_id):
            self.r.expire(session_id, timedelta(minutes=30), gt=True)
            return True

        return False
