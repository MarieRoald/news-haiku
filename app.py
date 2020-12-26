import flask
import random
import json

app = flask.Flask(__name__)

with open("haikus.json") as f:
    haikus = json.load(f)

@app.route("/")
def haiku():
    haiku_info = random.choice(haikus)
    haiku = haiku_info['haiku'].replace("\n", "<br />")
    html = f"<a href={haiku_info['link']}>{haiku}</a>"
    return html


if __name__ == "__main__":
    app.run()
