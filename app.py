global session, questions, app_name, config, templates
from flask import Flask, request, redirect, url_for, send_from_directory, render_template, jsonify
from flask_cors import CORS, cross_origin
import jinja2
import os

session = {"teams": [{"id": 1,
                      "name": "Test Team",
                      "score": 0
                      }],
           "cur_question": 1
}

with open("config.py") as config_file:
    code = compile(config_file.read(), "config.py", 'exec')
    exec(code)

app = Flask(__name__)
CORS(app)
app.debug = True
app.import_name = '.'
app.jinja_loader = jinja2.FileSystemLoader(os.getcwd() + "/static/themes/" + config["theme"] + "/templates/")


@app.route('/controller')
def controller():
    id = request.args.get("id")
    if id is None:
        return render_template('controller_init.html', question=questions[session["cur_question"]], **globals())
    else:
        return render_template('controller.html', question=questions[session["cur_question"]], **globals())


@app.route('/register_controller')
def register_controller():
    name = request.args.get("name")
    if name is not None and len(session["teams"]) < 4:
        id = len(session["teams"]) + 1
        team_dict = {"id": id,
                     "name": name,
                     "score": 0}
        app.logger.info(team_dict)
        session["teams"].append(team_dict)
        return jsonify(response="success",
                       id=id)
    else:
        return jsonify(response="failed")

@app.route('/send_answer')
def send_answer():
    answer = request.args.get("answer")
    team_id = request.args.get("team-id")
    correct = False
    question = questions[session["cur_question"]]
    correct_answer = question["correct_answer"]
    if answer is not None and team_id is not None:
        if answer == correct_answer:
            correct = True
            session["teams"][team_id+1]["score"] += 10
    return jsonify(correct=correct)

@app.route('/session_data')
def session_data():
    return jsonify(session=session, questions=questions)

@app.route('/')
def home():
    return render_template('quiz.html', question=questions[session["cur_question"]], **globals())


@app.route('/<path:path>')
def static_proxy(path):
  return app.send_static_file(path)


if __name__ == "__main__":
    app.run(host="0.0.0.0")
