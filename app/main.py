from flask import Flask, render_template, request, redirect
from sassutils.wsgi import SassMiddleware
from bson import json_util
import db

app = Flask(__name__)

app.wsgi_app = SassMiddleware(
    app.wsgi_app, {"main": ("static/sass", "static/css", "/static/css")}
)

# VIEWS


@app.route("/")
def home():
    collections = db.getCollectionsWithSongs()
    return render_template("home.html", collections=collections)


@app.route("/play/<song_id>")
def play(song_id):
    return render_template("play.html", song_id=song_id)


@app.route("/add/song", methods=["GET", "POST"])
def addSong():
    collections = db.getCollectionList()
    if request.method == "POST":
        try:
            song = {
                "title": request.form["title"],
                "collection_id": request.form["collection_id"],
                "lyrics": request.form["lyrics"],
            }
            return redirect("/play/" + str(db.addSong(song)))
        except Exception as e:
            print(e)
            return render_template("addSong.html", error=True, collections=collections)
    else:
        return render_template("addSong.html", collections=collections)

@app.route("/add/collection", methods=["GET", "POST"])
def addCollection():
    if request.method == "POST":
        try:
            collection = {
                "title": request.form["title"],
                "image": request.form["image"],
            }
            return redirect("/play/" + str(db.addCollection(collection)))
        except Exception as e:
            print(e)
            return render_template("addCollection.html", error=True)
    else:
        return render_template("addCollection.html",)


# API
@app.route("/api/getSong/<song_id>")
def getSong(song_id):
    song = db.getSongFromID(song_id)
    return json_util.dumps(song)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)

