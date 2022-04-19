from flask import Flask, request, jsonify, Blueprint
import mysql.connector as msc
from datetime import date
import bcrypt, threading, json
import redis
from authenticator import Auth

app = Flask(__name__)
db = msc.connect(
    host="167.71.231.52",
    username="project-work",
    password="mySQLpass",
    database="arcade",
)


class Database:
    def __init__(self):
        self.cursor = None
        self.cursor = db.cursor()
        t = threading.Thread(target=self.initialise)
        t.start()

    def execute(self, query):
        try:
            self.cursor.execute(query)
            response = self.cursor.fetchall()
            return response
        except Exception as e:
            print(e)
            print(query)
            return None

    def initialise(self):
        # Users
        cache.flushdb()
        # Monopoly Board Values
        query = f"SELECT * FROM monopoly_board_values"
        self.cursor.execute(query)
        details = {}
        for i in self.cursor.fetchall():
            details[int(i[1])] = i
        cache.set("monopoly_board_values", json.dumps(details))
        print("Loaded DB into cache")

    def data_change(self, query):
        try:
            self.cursor.execute(query)
            # self.cursor.fetchall()
            db.commit()

        except:
            db.rollback()


cache = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
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
    details = json.loads(cache.get("monopoly_board_values"))
    l = [i for i in details.values()]
    return jsonify(l), 200


@monopoly.route("/details/<string:pos>")
def details(pos):
    detail = json.loads(cache.get("monopoly_board_values"))
    if pos not in detail.keys():
        return jsonify("Not Found"), 404
    return jsonify(detail[pos]), 200


# endregion


req_authorisation.register_blueprint(monopoly, url_prefix="/monopoly")
req_authorisation.register_blueprint(chess, url_prefix="/chess")
app.register_blueprint(req_authorisation)
app.register_blueprint(authorisation)

app.run(
    ssl_context=(
        "./certificate.pem",
        "./key.pem",
    )
)
