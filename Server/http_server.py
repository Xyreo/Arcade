from flask import Flask, request, jsonify, Blueprint
from datetime import date
from authenticator import Auth
import mysql.connector as msc
import bcrypt, threading, json, pickle, os, sys, datetime, time
import hashlib
import redis
from dotenv import load_dotenv, find_dotenv

sys.stdout = open("log.txt", "w")

load_dotenv(find_dotenv())
password = os.getenv("password")
app = Flask(__name__)
db = msc.connect(
    host="167.71.231.52",
    username="project-work",
    password=password,
    database="arcade",
)


class Database:
    def __init__(self):
        cache.flushdb()

    def execute(self, query):
        if "select" in query.lower() and "user" not in query.lower():
            hash = hashlib.sha224(query.encode("utf-8")).hexdigest()
            key = "sql_cache" + hash
            key = key.encode("utf-8")
            if cache.get(key):
                return pickle.loads(cache.get(key))
            else:
                response = self.exec(query)
                cache.set(key, pickle.dumps(response))
                return response
        else:
            return self.exec(query)

    def exec(self, query):
        try:
            cursor = db.cursor()
            cursor.execute(query)
            response = cursor.fetchall()
            cursor.close()
            return response

        except Exception as e:
            print(f'{time.time()}: {e} Avoided, Query was "{query}"')

            return None

    def data_change(self, query):
        try:
            cursor.execute(query)
            # self.cursor.fetchall()
            db.commit()

        except:
            db.rollback()


cache = redis.Redis(host="localhost", port=6379, db=0)
cursor = Database()

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
    count = cursor.execute(f"SELECT * FROM user WHERE name = '{username}'")
    if len(count):
        return jsonify("User Already Exists"), 400
    password = bcrypt.hashpw(password, bcrypt.gensalt(12))
    password = str(password)[2:-1]
    doj = str(date.today())
    cursor.data_change(
        f'INSERT INTO user(name,doj,password) VALUES("{username}","{doj}","{password}")'
    )

    return jsonify("Success"), 200


@authorisation.route("/login", methods=["POST"])
def login():
    data = json.loads(request.data)
    username = data["username"]
    password = data["password"].encode("utf-8")

    storedpw = cursor.execute(f"SELECT password FROM user where name='{username}'")
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

    storedpw = cursor.execute(f"SELECT password FROM user where name='{username}'")
    if len(storedpw):
        if password == storedpw[0][0].encode("utf-8"):
            session = auth.add(username)
            return jsonify({"Token": session}), 200

    return jsonify("Either username or password is incorrect"), 400


@app.route("/exit")
def exit_flask():
    password = request.args.get("password").encode("utf-8")
    storedpw = cursor.execute(f'SELECT password,name FROM user where name = "root"')
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
    cursor.data_change(f'DELETE FROM user WHERE name="{auth.get_user(auth_token)}"')
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
    details = cursor.execute("SELECT * FROM monopoly_board_values")
    print(details)
    l = [i for i in details]
    return jsonify(l), 200


@monopoly.route("/details/<string:pos>")
def details(pos):
    detail = cursor.execute(f"SELECT * FROM monopoly_board_values where position={pos}")
    if len(detail) != 1:
        return jsonify("Not Found"), 404
    return jsonify(detail[0]), 200


# endregion


req_authorisation.register_blueprint(monopoly, url_prefix="/monopoly")
req_authorisation.register_blueprint(chess, url_prefix="/chess")
app.register_blueprint(req_authorisation)
app.register_blueprint(authorisation)

if __name__ == "__main__":
    app.run()
