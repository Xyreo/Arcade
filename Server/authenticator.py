import secrets
from datetime import timedelta

import redis


class Auth:
    def __init__(self):
        self.r = redis.Redis(host="localhost", port=6379, db=1)

    def add(self, name):
        for i in self.r.keys():
            if name == self.r.get(i).decode("utf-8"):
                self.r.delete(i)

        session_id = secrets.token_hex(16)
        while self.r.exists(session_id):
            session_id = secrets.token_hex(16)
        self.r.setex(session_id, timedelta(minutes=30), value=name)
        return session_id

    def end_session(self, session_id):
        if self.r.exists(session_id):
            self.r.delete(session_id)

    def get_user(self, session_id):
        user = self.r.get(session_id).decode("utf-8")
        if user:
            return user
        else:
            return None

    def __call__(self, session_id):
        if self.r.exists(session_id):
            self.r.expire(session_id, timedelta(minutes=30), xx=True)
            return True

        return False


if __name__ == "__main__":
    auth = Auth()
    print(auth('6p}ruUO5"VpP[)p|'))
