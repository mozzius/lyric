from flask import Flask, render_template, request, redirect, url_for
from flask_login import (
    LoginManager,
    login_user,
    login_required,
    current_user,
    logout_user,
)
from flask_socketio import SocketIO, emit, disconnect, join_room, close_room, leave_room
from sassutils.wsgi import SassMiddleware
from bson import json_util, ObjectId
import random

try:
    import db
except ImportError:
    import app.db as db

app = Flask(__name__)
socketio = SocketIO(app)
login = LoginManager(app)

# USER STUFF


class User:
    def __init__(self, user):
        self.username = user["username"]
        self.id = str(user["_id"])
        self.email = user["email"]

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id


@login.user_loader
def load_user(userid):
    user = db.getUser(userid)
    if user:
        return User(user)
    else:
        return None


@login.unauthorized_handler
def unauthHandler():
    return redirect(url_for("login"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        form = request.form
        user_id = db.verifyUser(form["email"], form["password"])
        print(user_id)
        if user_id != None:
            user = db.getUser(user_id)
            login_user(User(user))
            return redirect("/")
        else:
            return render_template("login.html", error=True)
    else:
        if current_user.is_authenticated:
            return redirect("/")
        else:
            return render_template("login.html", error=False)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        form = request.form
        if form["password"] == form["repeatPassword"]:
            user_id = db.addUser(form["username"], form["email"], form["password"])
            if user_id != None:
                user = db.getUser(user_id)
                login_user(User(user))
                return redirect("/")
            else:
                return render_template("signup.html", error=True)
        else:
            print("password not repeated correctly")
            return render_template("signup.html", error=True)
    else:
        if current_user.is_authenticated:
            return redirect("/")
        else:
            return render_template("signup.html", error=False)


# VIEWS


@app.route("/")
def home():
    collections = db.getCollectionsWithSongs()
    return render_template("home.html", collections=collections)


@app.route("/play/<song_id>")
def play(song_id):
    return render_template("play.html", song_id=song_id)


@app.route("/random/<collection_id>")
def playRandom(collection_id):
    collection = db.getCollectionWithSongsFromID(collection_id)
    song_id = random.choice(collection["songs"])["_id"]
    return render_template("play.html", song_id=song_id, hidden=True)


@app.route("/collection/<collection>")
def viewCollection(collection):
    collection = db.getCollectionWithSongsFromID(collection)
    return render_template("collection.html", collection=collection)


@app.route("/add/song", methods=["GET", "POST"])
@login_required
def addSong():
    collections = db.getCollectionList()
    if request.method == "POST":
        try:
            song = {
                "title": request.form["title"],
                "collection_id": request.form["collection_id"],
                "lyrics": request.form["lyrics"],
                "user_id": ObjectId(current_user.get_id()),
            }
            return redirect("/play/" + str(db.addSong(song)))
        except Exception as e:
            print(e)
            return render_template("addSong.html", collections=collections, error=True)
    else:
        return render_template("addSong.html", collections=collections)


@app.route("/add/collection", methods=["GET", "POST"])
@login_required
def addCollection():
    if request.method == "POST":
        try:
            collection = {
                "title": request.form["title"],
                "image": request.form["image"],
                "user_id": ObjectId(current_user.get_id()),
            }
            return redirect("/collection/" + str(db.addCollection(collection)))
        except Exception as e:
            print(e)
            return render_template("addCollection.html", error=True)
    else:
        return render_template("addCollection.html")


# MULTIPLAYER


@app.route("/room", methods=["GET", "POST"])
@login_required
def roomMenu():
    collections = db.getCollectionList()
    if request.method == "POST":
        room = None
        try:
            room = request.form.get("name")
            if request.form.get("random"):
                songs = db.getSongsFromCollectionID(request.form.get("collection_id"))
                song_id = random.choice(songs)["_id"]
            else:
                song_id = request.form.get("song_id")
            return redirect("/room/" + str(db.createRoom(room, song_id, request.form.get("random"))))
        except Exception as e:
            print(e)
            return render_template(
                "room.html",
                collections=collections,
                error=("An error occurred creating a room"),
            )
    else:
        return render_template("room.html", collections=collections)


@app.route("/room/<room_id>")
@login_required
def playRoom(room_id):
    room = db.getRoom(room_id)
    if room == None:
        collections = db.getCollectionList()
        return render_template(
            "room.html", collections=collections, error="Error joining room :("
        )
    elif current_user.get_id() not in [x["id"] for x in room["members"]]:
        room = db.joinRoom(room["name"])
    return render_template(
        "play.html", multiplayer=True, hidden=room["random"], song_id=room["song_id"], room=str(room["_id"])
    )


@app.route("/join", methods=["GET"])
@login_required
def roomJoin():
    name = request.args.get("name")
    room = db.joinRoom(name)
    if room == None:
        collections = db.getCollectionList()
        return render_template(
            "room.html",
            collections=collections,
            error=("Room '{}' not found".format(name)),
        )
    else:
        return redirect("/room/" + str(room["_id"]))


@socketio.on("connect", namespace="/multiplayer")
def connectHandler():
    if not current_user.is_authenticated:
        return False  # not allowed here
    else:
        print("User joined: {}".format(current_user.username))


@socketio.on("join", namespace="/multiplayer")
def joinHandler(data):
    print(current_user.username + " wants to join room " + data["room"])
    join_room(data["room"])
    emit(
        "members",
        {"members": db.getRoomMembers(data["room"])},
        broadcast=True,
        namespace="/multiplayer",
    )


@socketio.on("send update", namespace="/multiplayer")
def updateHandler(data):
    db.updateRoomMemberScores(current_user.get_id(), data["room"], data)
    emit(
        "update",
        {
            "id": current_user.get_id(),
            "username": current_user.username,
            "numerator": data["numerator"],
            "denominator": data["denominator"],
        },
        room=data["room"],
        broadcast=True,
        namespace="/multiplayer",
    )


@socketio.on("client won", namespace="/multiplayer")
def victoryHandler(data):
    emit(
        "victory",
        {"winner": current_user.username, "time": data["time"]},
        room=data["room"],
        broadcast=True,
        namespace="/multiplayer",
    )
    close_room(data["room"])
    db.deleteRoom(data["room"])


@socketio.on("disconnect", namespace="/multiplayer")
def disconnectHandler():
    print("{} has left".format(current_user.username))
    try:
        leave_room(str(db.leaveRoom(current_user.get_id())["_id"]))
    except Exception as e:
        print(e)


# API


@app.route("/api/getSong/<song_id>")
def getSong(song_id):
    song = db.getSongFromID(song_id)
    return json_util.dumps(song)


@app.route("/api/getCollection/<collection_id>")
def getCollection(collection_id):
    collection = db.getCollectionWithSongsFromID(collection_id)
    return json_util.dumps(collection)


if __name__ == "__main__":
    app.secret_key = "localhost"
    app.wsgi_app = SassMiddleware(
        app.wsgi_app, {"main": ("static/sass", "static/css", "/static/css")}
    )
    socketio.run(app, host="0.0.0.0", port=8000, debug=True)

