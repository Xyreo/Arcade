import base64
import datetime
import json
import os
import time
from datetime import date

import bcrypt
import mysql.connector as msc
import redis
from dotenv import find_dotenv, load_dotenv
from flask import Blueprint, Flask, jsonify, request

from authenticator import Auth

app = Flask(__name__)
load_dotenv(find_dotenv())
password = os.getenv("password")
PFP_PATH = "pfp"


class Database:
    def __init__(self):
        cache.flushdb()
        self.db = msc.connect(
            host="167.71.231.52",
            username="project-work",
            password=password,
            database="arcade",
            autocommit=True,
        )

    def execute(self, query, multi=False):
        while True:
            try:
                cursor = self.db.cursor()
                response = []
                if multi:
                    for result in cursor.execute(query, multi=True):
                        if result.with_rows:
                            print(result.fetchall())
                else:
                    cursor.execute(query)
                    response = cursor.fetchall()
                cursor.close()
                return response

            except msc.OperationalError:
                self.db = msc.connect(
                    host="167.71.231.52",
                    username="project-work",
                    password=password,
                    database="arcade",
                    autocommit=True,
                )
            except Exception as e:
                print(f'{time.time()}: {e} Avoided, Query was "{query}"')
                return None

    def data_change(self, query, multi=True):
        try:
            self.execute(query, multi=multi)
            # self.cursor.fetchall()
            self.db.commit()

        except:
            self.db.rollback()


cache = redis.Redis(host="localhost", port=6379, db=0)
db = Database()

monopoly = Blueprint("monopoly", __name__)
chess = Blueprint("chess", __name__)
req_authorisation = Blueprint("req_authorisation", __name__)
authorisation = Blueprint("authorisation", __name__)
auth = Auth()


# region main-stuff
@app.route("/ping")
def ping():
    return jsonify("Pong")


@app.before_request
def logging():
    print(datetime.datetime.now().strftime("[%m/%d/%Y %H:%M:%S]-"), request)


@authorisation.before_request
def check_authdata():
    try:
        data = json.loads(request.data)
        username = data["username"]
        password = data["password"].encode("utf-8")
    except KeyError:
        return jsonify("Wrong Data"), 400
    except json.decoder.JSONDecodeError:
        return jsonify("Wrong Data"), 400


@authorisation.route("/register", methods=["POST"])
def register():
    data = json.loads(request.data)
    username = data["username"]
    password = data["password"].encode("utf-8")
    img = data["image"]
    count = db.execute(f"SELECT * FROM user WHERE name = '{username}'")
    if len(count):
        return jsonify("User Already Exists"), 400
    password = bcrypt.hashpw(password, bcrypt.gensalt(12))
    password = str(password)[2:-1]
    doj = str(date.today())
    db.data_change(
        f'INSERT INTO user(name,doj,password) VALUES("{username}","{doj}","{password}")'
    )
    save_img(img, username)

    return jsonify("Success"), 200


@authorisation.route("/login", methods=["POST"])
def login():
    data = json.loads(request.data)
    username = data["username"]
    password = data["password"].encode("utf-8")

    storedpw = db.execute(f"SELECT password FROM user where name='{username}'")
    print(storedpw)
    if len(storedpw):
        if bcrypt.checkpw(password, storedpw[0][0].encode("utf-8")):
            session = auth.add(username)
            if not session:
                return jsonify(), 406
            return jsonify({"Token": session, "Password": storedpw[0][0]}), 200

    return jsonify("Either username or password is incorrect"), 400


@authorisation.route("/remember_login", methods=["POST"])
def remember_login():
    data = json.loads(request.data)
    username = data["username"]
    password = data["password"].encode("utf-8")

    storedpw = db.execute(f"SELECT password FROM user where name='{username}'")
    if len(storedpw):
        if password == storedpw[0][0].encode("utf-8"):
            session = auth.add(username)
            if not session:
                return jsonify(), 406
            return jsonify({"Token": session}), 200

    return jsonify("Either username or password is incorrect"), 400


@app.route("/exit")
def exit_flask():
    password = request.args.get("password").encode("utf-8")
    storedpw = db.execute(f'SELECT password,name FROM user where name = "root"')
    if bcrypt.checkpw(password, storedpw[0][0].encode("utf-8")):
        db.close()

    return jsonify("Wrong Password"), 400


@req_authorisation.before_request
def check_session():
    authorisation = request.headers.get("Authorization")
    if not authorisation:
        return jsonify("Insert authorisation token"), 401

    auth_token = authorisation.split()
    if auth_token[0] != "Bearer" or len(auth_token) != 2:
        return jsonify("Only Bearer Token is allowed"), 401
    if not auth(auth_token[1]):
        return jsonify("Operation not permitted"), 403


@req_authorisation.route("/delete_user", methods=["DELETE"])
def delete_user():
    authorisation = request.headers.get("Authorization")
    auth_token = authorisation.split()[1]
    db.data_change(
        f'DELETE FROM user WHERE name="{auth.get_user_from_session(auth_token)}"'
    )
    auth.end_session(auth_token)
    return jsonify("Success"), 200


@req_authorisation.route("/logout", methods=["POST"])
def logout():
    session_id = request.headers.get("Authorization").split()[1]
    auth.end_session(session_id)
    return jsonify("Success"), 200


@req_authorisation.route("/change_password", methods=["POST"])
def change_password():
    data = json.loads(request.data)
    username = auth.get_user_from_session(
        request.headers.get("Authorization").split()[1]
    )
    new_password = data["newpass"].encode("utf-8")
    p = str(bcrypt.hashpw(new_password, bcrypt.gensalt(12)))[2:-1]
    db.data_change(f"UPDATE user SET password='{p}' WHERE name='{username}'")
    return jsonify("Success"), 200


@req_authorisation.route("/fetch_pfp/<string:name>")
def fetch_pfp(name):
    pfp = load_img(name)
    if not pfp:
        return jsonify("User Not Found"), 404
    return jsonify({"image": pfp}), 200


@req_authorisation.route("/change_pfp", methods=["POST"])
def change_pfp():
    data = json.loads(request.data)
    username = auth.get_user_from_session(
        request.headers.get("Authorization").split()[1]
    )
    img = data["image"]
    save_img(img, username)
    return jsonify("Success"), 200


# endregion


# region Monopoly
@monopoly.route("/details")
def list_details():
    details = db.execute("SELECT * FROM monopoly_board_values")
    l = [i for i in details]
    return jsonify(l), 200


@monopoly.route("/details/<string:pos>")
def details(pos):
    detail = db.execute(f"SELECT * FROM monopoly_board_values where position={pos}")
    if len(detail) != 1:
        return jsonify("Not Found"), 404
    return jsonify(detail[0]), 200


@monopoly.route("/add_game", methods=["POST"])
def monopoly_game_add():
    try:
        data = json.loads(request.data)
        winner = data["winner"]
        result = data["result"]

        players = data["players"]
        result = str(result).replace("'", '"')
        s = "insert into game_user(user,game) values "
        for i in players:
            s += f"('{i}',@v1),"
        s = s[:-1] + ";"

        q = f"""SET @v1 := (SELECT IFNULL(srno,0) FROM game ORDER BY srno DESC LIMIT 1)+1;
        insert into game(srno,type,result,winner) values (@v1,'MNPLY','{result}','{winner}');
        {s}"""
        db.data_change(q, multi=True)
        return jsonify("Success"), 200
    except Exception as e:
        print(e)
        return jsonify("Bad Request"), 400


@monopoly.route("/stats/<string:name>")
def monopoly_stats(name):
    q = f'select user.srno,user.name,game.srno,game.result,game.winner from user inner join game_user on game_user.user=user.name inner join game on game_user.game = game.srno where user.name="{name}" and game.type="MNPLY";'
    details = db.execute(q)
    try:
        if not (details or len(details)):
            return jsonify("Bad Request"), 400
        res = []
        for i in details:
            res.append((i[2], eval(i[3]), i[4]))
        return jsonify(res), 200
    except Exception as e:
        return jsonify(e), 400


@monopoly.route("/leaderboard")
def monopoly_leaderboard():
    det = db.execute(
        "select user.srno, user.name, game.srno, game.result, game.winner from user inner join game_user on game_user.user=user.name inner join game on game_user.game = game.srno where game.type='MNPLY';"
    )
    # cursor.execute('drop table monopoly_board_values')
    try:
        res = {}
        for i in det:
            if i[0] in res:
                res[i[0]]["games"].append((i[2], eval(i[3]), i[4]))
            else:
                res[i[0]] = {"name": i[1], "games": [(i[2], eval(i[3]), i[4])]}
        send = {}
        for i, j in res.items():
            g = [nw[1][str(i)] for nw in j["games"]]
            send[j["name"]] = max(g)

        return jsonify(send), 200

    except Exception as e:
        return jsonify(e), 404


# endregion

# region Chess
@chess.route("/add_game", methods=["POST"])
def chess_game_add():
    try:
        data = json.loads(request.data)
        winner = data["winner"]
        result = data["result"]

        players = data["players"]
        result = str(result).replace("'", '"')
        s = "insert into game_user(user,game) values "
        for i in players:
            s += f"('{i}',@v1),"
        s = s[:-1] + ";"

        q = f"""SET @v1 := (SELECT IFNULL(srno,0) FROM game ORDER BY srno DESC LIMIT 1)+1;
        insert into game(srno,type,result,winner) values (@v1,'CHESS','{result}','{winner}');
        {s}"""
        db.data_change(q, multi=True)
        return jsonify("Succes"), 200
    except Exception as e:
        print(e)
        return jsonify("Bad Req"), 400


@chess.route("/stats/<string:name>")
def chess_stats(name):
    q = f'select user.srno,user.name,game.srno,game.result,game.winner from user inner join game_user on game_user.user=user.name inner join game on game_user.game = game.srno where user.name="{name}" and game.type="CHESS";'
    details = db.execute(q)
    try:
        if not (details or len(details)):
            return jsonify("Bad Request"), 400
        res = []
        for i in details:
            res.append((i[2], eval(i[3]), i[4]))
        return jsonify(res), 200
    except Exception as e:
        return jsonify(e), 400


@chess.route("/leaderboard")
def chess_leaderboard():
    det = db.execute(
        "select user.srno, user.name, game.srno, game.result, game.winner from user inner join game_user on game_user.user=user.name inner join game on game_user.game = game.srno where game.type='CHESS';"
    )
    # cursor.execute('drop table monopoly_board_values')
    try:
        res = {}
        for i in det:
            if i[0] in res:
                res[i[0]]["games"].append((i[2], eval(i[3]), i[4]))
            else:
                res[i[0]] = {"name": i[1], "games": [(i[2], eval(i[3]), i[4])]}
        send = {}
        for i, j in res.items():
            pt = 0
            for game in j["games"]:
                if j["name"] == game[2]:
                    pt += 1
                elif game[2] == "none":
                    pt += 0.5
            send[j["name"]] = pt
        return jsonify(send), 200

    except Exception as e:
        return jsonify(e), 404


def save_img(img, user):
    try:
        with open(os.path.join(PFP_PATH, f"{user}_pfp.png"), "wb") as f:
            f.write(base64.b64decode(img.encode("latin1")))
    except Exception as e:
        print("Error while saving image-", e)


def load_img(user):
    if os.path.isfile(os.path.join(PFP_PATH, f"{user}_pfp.png")):
        try:
            with open(os.path.join(PFP_PATH, f"{user}_pfp.png"), "rb") as f:
                return base64.b64encode(f.read()).decode("latin1")
        except Exception as e:
            print("Error while loading image-", e)
    else:
        try:
            with open(os.path.join(PFP_PATH, f"default_pfp.png"), "rb") as f:
                with open(os.path.join(PFP_PATH, f"{user}_pfp.png"), "wb") as f2:
                    f2.write(f.read())
                f.seek(0)
                return base64.b64encode(f.read()).decode("latin1")
        except Exception as e:
            print("Error while loading image-", e)


# endregion
req_authorisation.register_blueprint(monopoly, url_prefix="/monopoly")
req_authorisation.register_blueprint(chess, url_prefix="/chess")
app.register_blueprint(req_authorisation)
app.register_blueprint(authorisation)

if __name__ == "__main__":
    app.run()
