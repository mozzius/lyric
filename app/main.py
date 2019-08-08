from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/play/<song>")
def play(song):
    return render_template("play.html", song=song)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)

