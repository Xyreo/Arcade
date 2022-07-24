import secrets
from datetime import timedelta

import redis

time = 20


class Auth:
    def __init__(self):
        self.r = redis.Redis(host="localhost", port=6379, db=1)

    def add(self, name):
        if self.r.exists(name.lower()):
            return False

        session_id = secrets.token_hex(16)
        while self.r.exists(session_id):
            session_id = secrets.token_hex(16)
        self.r.setex(session_id, timedelta(minutes=time), value=name)
        self.r.setex(name.lower(), timedelta(minutes=time), value=session_id)
        return session_id

    def end_session(self, session_id):
        if self.r.exists(session_id):
            self.r.delete(self.r.get(session_id).decode("utf-8").lower())
            self.r.delete(session_id)

    def end_session_by_name(self, name):
        if self.r.exists(name.lower()):
            self.r.delete(self.r.get(name.lower()))
            self.r.delete(name.lower())

    def get_user_from_session(self, session_id):
        user = self.r.get(session_id)
        if user:
            return user.decode("utf-8").lower()
        else:
            return None

    def __call__(self, session_id, expire=time):
        if self.r.exists(session_id):
            self.r.expire(name=session_id, time=timedelta(minutes=expire))
            self.r.expire(name=self.r.get(session_id), time=timedelta(minutes=expire))
            return True
        return False
