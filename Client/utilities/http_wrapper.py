import requests


class Http:
    POST = "post"
    GET = "get"
    PUT = "put"
    DELETE = "delete"

    def __init__(self, address):
        self.address = address
        self.TOKEN = None

    def login_send(self, method, username, password, remember_me=False):
        data = {"username": username, "password": password}
        r = self.send(Http.POST, method, data=data)
        if r.status_code == 200:
            self.TOKEN = r.json()["Token"]
            if remember_me:
                return r.json()["Password"]
            return 1
        elif r.status_code == 406:
            return -1
        return 0

    def login(self, username, password, remember_me=False, remember_login=False):
        if remember_login:
            return self.login_send("remember_login", username, password)
        return self.login_send("login", username, password, remember_me=remember_me)

    def register(self, username, password, image):
        data = {"username": username, "password": password, "image": image}
        r = self.send(Http.POST, "register", data=data)
        if r.status_code == 200:
            return True
        return False

    def change_password(self, password):
        r = self.auth_send("post", "change_password", {"newpass": password})
        if r.status_code == 200:
            return True

    def del_user(self):
        path = "delete_user"
        r = self.auth_send(Http.DELETE, path)
        if r.status_code != 200:
            return False
        return True

    def logout(self):
        path = "logout"
        r = self.auth_send(Http.POST, path)
        if r.status_code != 200:
            return False
        return True

    def mply_details(self, pos=None):
        path = "details"
        if pos != None:
            path += "/" + str(pos)
        r = self.game_send(Http.GET, "monopoly", path)
        if r.status_code == 404:
            return -1
        elif r.status_code != 200:
            return False
        else:
            return r.json()

    def change_pfp(self, img):
        r = self.auth_send("post", "change_pfp", {"image": img})
        if r.status_code == 200:
            return True

    def fetch_pfp(self, name):
        r = self.auth_send("get", f"fetch_pfp/{name}")
        if r.status_code == 200:
            return r.json()["image"]
        elif r.status_code == 404:
            return False

    def addgame(self, game, winner, result, players):
        r = self.game_send(
            "post",
            game,
            "add_game",
            {"winner": winner, "result": result, "players": players},
        )
        return r.json()

    def stats(self, game, name):
        r = self.game_send("get", game, f"stats/{name}")
        return r.json()

    def leaderboard(self, game):
        r = self.game_send("get", game, f"leaderboard")
        return r.json()

    def game_send(self, method, game, path, data=None):
        path = f"{game.lower()}/{path}"
        r = self.auth_send(method, path, data)
        return r

    def auth_send(self, method, path, data=None):
        if not self.TOKEN:
            return Response(400, "Please Login")

        headers = {"Authorization": "Bearer " + self.TOKEN}
        r = self.send(method, path, data, headers=headers)
        return r

    def send(self, method, path, data=None, headers={}):
        url = self.address + "/" + path
        r = None

        if method == "post":
            r = requests.post(url, json=data, headers=headers)
        elif method == "put":
            r = requests.put(url, json=data, headers=headers)
        elif method == "get":
            r = requests.get(url, headers=headers)
        elif method == "delete":
            r = requests.delete(url, headers=headers)
        else:
            return "INVALID REQUEST"
        return r


class Response:
    def __init__(self, code, body):
        self.status_code = code
        self.body = body

    def json(self):
        return self.body


if __name__ == "__main__":
    app = Http("http://localhost:5000")
