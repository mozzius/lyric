from flask import Flask, render_template
from sassutils.wsgi import SassMiddleware

app = Flask(__name__)

app.wsgi_app = SassMiddleware(
    app.wsgi_app, {"main": ("static/sass", "static/css", "/static/css")}
)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/play/<song>")
def play(song):
    return render_template("play.html", song=song)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)

