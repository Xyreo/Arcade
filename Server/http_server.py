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


class Database:
    def __init__(self):
        cache.flushdb()
        self.db = msc.connect(
            host="167.71.231.52",
            username="project-work",
            password=password,
            database="arcade",
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
    count = db.execute(f"SELECT * FROM user WHERE name = '{username}'")
    if len(count):
        return jsonify("User Already Exists"), 400
    password = bcrypt.hashpw(password, bcrypt.gensalt(12))
    password = str(password)[2:-1]
    doj = str(date.today())
    db.data_change(
        f'INSERT INTO user(name,doj,password) VALUES("{username}","{doj}","{password}")'
    )

    return jsonify("Success"), 200


@authorisation.route("/login", methods=["POST"])
def login():
    data = json.loads(request.data)
    username = data["username"]
    password = data["password"].encode("utf-8")

    storedpw = db.execute(f"SELECT password FROM user where name='{username}'")
    if len(storedpw):
        if bcrypt.checkpw(password, storedpw[0][0].encode("utf-8")):
            session = auth.add(username)
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
    db.data_change(f'DELETE FROM user WHERE name="{auth.get_user(auth_token)}"')
    auth.end_session(auth_token)
    return jsonify("Success"), 200


@req_authorisation.route("/logout", methods=["POST"])
def logout():
    session_id = request.headers.get("Authorization").split()[1]
    auth.end_session(session_id)
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
        winner = int(data["winner"])
        result = data["result"]

        players = data["players"]
        result = str(result).replace("'", '"')
        s = "insert into game_user(user,game) values "
        for i in players:
            s += f"({i},@v1),"
        s = s[:-1] + ";"

        q = f"""SET @v1 := (SELECT uuid FROM game ORDER BY uuid DESC LIMIT 1)+1;
        insert into game(type,result,winner,uuid) values ('MPY','{result}',{winner},@v1);
        {s}"""
        db.data_change(q, multi=True)
        return jsonify("Success"), 200
    except Exception as e:
        print(e)
        return jsonify("Bad Request"), 400


@monopoly.route("/stats/<int:uuid>")
def monopoly_stats(uuid):
    q = f'select user.uuid,user.name,game.uuid,game.result,game.winner from user inner join game_user  on game_user.user=user.uuid inner join game on  game_user.game = game.uuid where user.uuid={uuid} and game.type="MPY";'
    details = db.execute(q)
    if len(details):
        return jsonify(details), 200
    return jsonify("Bad Request"), 400


@monopoly.route("/leaderboard")
def monopoly_leaderboard():
    det = db.execute(
        "select user.uuid, user.name, game.uuid, game.result, game.winner from user inner join game_user  on game_user.user=user.uuid inner join game on game_user.game = game.uuid where game.type='MPY';"
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
        winner = int(data["winner"])
        result = data["result"]

        players = data["players"]
        result = str(result).replace("'", '"')
        s = "insert into game_user(user,game) values "
        for i in players:
            s += f"({i},@v1),"
        s = s[:-1] + ";"

        q = f"""SET @v1 := (SELECT uuid FROM game ORDER BY uuid DESC LIMIT 1)+1;
        insert into game(type,result,winner,uuid) values ('CHS','{result}',{winner},@v1);
        {s}"""
        db.data_change(q, multi=True)
        return jsonify("Succes"), 200
    except Exception as e:
        print(e)
        return jsonify("Bad Req"), 400


@chess.route("/stats/<int:uuid>")
def chess_stats(uuid):
    q = f'select user.uuid,user.name,game.uuid,game.result,game.winner from user inner join game_user  on game_user.user=user.uuid inner join game on game_user.game = game.uuid where user.uuid={uuid} and game.type="CHS";'
    details = db.execute(q)
    if len(details):
        return jsonify(details), 200
    return jsonify("Bad Request"), 400


@chess.route("/leaderboard")
def chess_leaderboard():
    det = db.execute(
        "select user.uuid, user.name, game.uuid, game.result, game.winner from user inner join game_user  on game_user.user=user.uuid inner join game on game_user.game = game.uuid where game.type='CHS';"
    )
    # cursor.execute('drop table monopoly_board_values')
    try:
        res = {}
        for i in det:
            if i[0] in res:
                res[i[0]]["games"].append((i[2], eval(i[3]), i[4]))
            else:
                res[i[0]] = {"name": i[1], "games": [(i[2], eval(i[3]), i[4])]}
        # print(tab.tabulate(cursor))
        # print(res)
        send = {}
        for i, j in res.items():
            g = [1 for nw in j["games"] if int(nw[2]) == i]
            send[j["name"]] = len(g)
        return jsonify(send), 200

    except Exception as e:
        return jsonify(e), 404


# endregion
req_authorisation.register_blueprint(monopoly, url_prefix="/monopoly")
req_authorisation.register_blueprint(chess, url_prefix="/chess")
app.register_blueprint(req_authorisation)
app.register_blueprint(authorisation)

if __name__ == "__main__":
    app.run()
