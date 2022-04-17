from concurrent.futures import wait
from flask import Flask, request, jsonify, Blueprint
from flask_mysqldb import MySQL
from datetime import date
import bcrypt, random

app = Flask(__name__)
app.config["MYSQL_HOST"] = "167.71.231.52"
app.config["MYSQL_USER"] = "project-work"
app.config["MYSQL_PASSWORD"] = "mySQLpass"
app.config["MYSQL_DB"] = "arcade"
mysql = MySQL(app)

monopoly = Blueprint("monopoly", __name__)
chess = Blueprint("chess", __name__)

sessions = {}


def generate_id():
    id = ""
    for i in range(16):
        id += chr(random.randint(33, 125))
    return id


def assign_session(uuid):
    session_id = generate_id()
    while session_id in sessions.keys():
        session_id = generate_id()
    sessions[session_id] = uuid
    return session_id


@app.route("/ping")
def ping():
    return jsonify("Pong")


@app.route("/register/", methods=["POST"])
def register():
    cursor = mysql.connection.cursor()

    name = request.args.get("name").lower()

    query = f'SELECT COUNT(*) FROM user WHERE name="{name}"'
    cursor.execute(query)
    if cursor.fetchall()[0][0]:
        return jsonify("User Already Exists"), 400

    password = request.args.get("password").encode("utf-8")
    password = bcrypt.hashpw(password, bcrypt.gensalt(12))
    password = str(password)[2:-1]

    doj = str(date.today())

    query = f'INSERT INTO user(name,doj,password) VALUES("{name}","{doj}","{password}")'
    cursor.execute(query)
    mysql.connection.commit()
    return jsonify("SUCCESS"), 200


@app.route("/login/", methods=["GET"])
def login():
    cursor = mysql.connection.cursor()

    name = request.args.get("name").lower()
    password = request.args.get("password").encode("utf-8")
    query = f'SELECT PASSWORD FROM user WHERE name="{name}"'
    cursor.execute(query)
    storedpw = cursor.fetchall()
    if storedpw:
        result = bcrypt.checkpw(password, storedpw[0][0].encode("utf-8"))
        if result:
            return jsonify("SUCCESS"), 200
        """else:
            return jsonify("WRONG_PASSWORD"), 400"""
    return jsonify("ERROR"), 400


@monopoly.route("/details")
def list_details():
    cursor = mysql.connection.cursor()
    query = f"SELECT * FROM monopoly_board_values"
    cursor.execute(query)
    details = cursor.fetchall()
    # details = ""
    return jsonify(details), 200


@monopoly.route("/details/<int:pos>")
def details(pos):
    cursor = mysql.connection.cursor()
    query = f"SELECT * FROM monopoly_board_values WHERE position={pos}"
    cursor.execute(query)
    details = cursor.fetchall()
    if len(details) == 0:
        return jsonify("NOT FOUND"), 404
    return jsonify(details[0]), 200


app.register_blueprint(monopoly, url_prefix="/monopoly")
app.register_blueprint(chess, url_prefix="/chess")
app.run(
    ssl_context=(
        "./certificate.pem",
        "./key.pem",
    )
)
