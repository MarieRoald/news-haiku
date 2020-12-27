import json
import random

import flask


__author__ = "Marie Roald & Yngve Mardal Moe"


app = flask.Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True


@app.route("/")
def haiku():
    with open("static/haikus.json") as f:
        haikus = json.load(f)

    haiku_info = random.choice(haikus)
    haiku = haiku_info["haiku"].splitlines()

    return flask.render_template("haiku.html", url=haiku_info["link"], haiku=haiku)


if __name__ == "__main__":
    app.run()
