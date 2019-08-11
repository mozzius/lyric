from flask import Flask, render_template, request, redirect, url_for
from flask_login import (
    LoginManager,
    login_user,
    login_required,
    current_user,
    logout_user,
)
from sassutils.wsgi import SassMiddleware
from bson import json_util, ObjectId

try:
    import db
except ImportError:
    import app.db as db

app = Flask(__name__)
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
            return render_template("addSong.html", error=True, collections=collections)
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


# API
@app.route("/api/getSong/<song_id>")
def getSong(song_id):
    song = db.getSongFromID(song_id)
    return json_util.dumps(song)


if __name__ == "__main__":
    app.wsgi_app = SassMiddleware(
        app.wsgi_app, {"main": ("static/sass", "static/css", "/static/css")}
    )
    app.secret_key = "localhost"
    app.run(debug=True, host="0.0.0.0", port=8000)

