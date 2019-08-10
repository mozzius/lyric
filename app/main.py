from flask import Flask, render_template
from sassutils.wsgi import SassMiddleware
from bson import json_util
import db

app = Flask(__name__)

app.wsgi_app = SassMiddleware(
    app.wsgi_app,
    {"main": ("static/sass", "static/css", "/static/css")}
)

# VIEWS

@app.route("/")
def home():
    songs = db.getSongList()
    return render_template("home.html", songs=songs)


@app.route("/play/<song_id>")
def play(song_id):
    return render_template("play.html", song_id=song_id)

# API
@app.route("/api/getSong/<song_id>")
def getSong(song_id):
    song = db.getSongFromID(song_id)
    return json_util.dumps(song)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)