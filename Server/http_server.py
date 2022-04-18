from flask import Flask, request, jsonify, Blueprint
import mysql.connector as msc
from datetime import date
import bcrypt, random, time, threading, json
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

    def insert(self, query):
        t = threading.Thread(target=self.threaded, args=(query,))
        t.start()

    def threaded(self, query):
        try:
            self.cursor.execute(query)
            self.cursor.fetchall()
            db.commit()

        except:
            db.rollback()


cache = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
cursor = Database()

monopoly = Blueprint("monopoly", __name__)
chess = Blueprint("chess", __name__)
authorisation = Blueprint("authorisation", __name__)
auth = Auth()


# region main-stuff


@app.route("/ping")
def ping():
    return jsonify("Pong")


@app.route("/register", methods=["POST"])
def register():
    name = request.args.get("name").lower()
    count = cursor.execute("SELECT * FROM user WHERE name = {name}")
    if not len(count):
        return jsonify("User Already Exists"), 400

    password = request.args.get("password").encode("utf-8")
    password = bcrypt.hashpw(password, bcrypt.gensalt(12))
    password = str(password)[2:-1]
    doj = str(date.today())
    cursor.insert(
        f'INSERT INTO user(name,doj,password) VALUES("{name}","{doj}","{password}")'
    )

    return jsonify("SUCCESS"), 200


@app.route("/login", methods=["GET"])
def login():
    name = request.args.get("name").lower()
    password = request.args.get("password").encode("utf-8")
    storedpw = cursor.execute(f"SELECT password FROM user where name='{name}'")
    if len(storedpw):
        if bcrypt.checkpw(password, storedpw[0][0].encode("utf-8")):
            session = auth.add(name)
            return jsonify({"TOKEN": session}), 200

    return jsonify("ERROR"), 400


@app.route("/delete_user", methods=["GET"])
def delete_user():
    name = request.args.get("name").lower()
    password = request.args.get("password").encode("utf-8")
    storedpw = cursor.execute(f"SELECT password FROM user where name='{name}'")
    if len(storedpw):
        if bcrypt.checkpw(password, storedpw[0][0].encode("utf-8")):
            session = auth.add(name)
            return jsonify({"TOKEN": session}), 200
    return jsonify("WRONG PASSWORD")


@app.route("/exit")
def exit_flask():
    password = request.args.get("password").encode("utf-8")
    storedpw = cursor.execute(f'SELECT password,name FROM user where name = "root"')
    if bcrypt.checkpw(password, storedpw[0][0].encode("utf-8")):
        db.close()

    return jsonify("Wrong Password"), 400


@authorisation.before_request
def check_session():
    session_id = request.headers.get("Authorization").split()[1]
    if not auth(session_id):
        return jsonify("You Can't access this"), 403


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
    print(detail)
    if pos not in detail.keys():
        return jsonify("Not Found"), 404
    return jsonify(detail[pos]), 200


# endregion


authorisation.register_blueprint(monopoly, url_prefix="/monopoly")
authorisation.register_blueprint(chess, url_prefix="/chess")
app.register_blueprint(authorisation)

app.run(
    ssl_context=(
        "./certificate.pem",
        "./key.pem",
    )
)
