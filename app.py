global session, questions, config, templates
from flask import Flask, request, redirect, url_for, send_from_directory, render_template, jsonify
from flask_cors import CORS, cross_origin
import jinja2
import os
import sys

session = {"teams": [],
           "cur_question": 0,
           "status": "waiting-for-teams" # Either "waiting-for-teams", "accepting-answers", "not-accepting-answers" or "endgame"
}

"""
Example of team:
{"id": 0,
"name": "Test Team",
"score": 0,
"answer": {"question" : -1, "answer": 0}
}
"""

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
    try:
        id = int(request.args.get("id"))
        team_exists = False
        for team in session["teams"]:
            if team["id"] == id:
                team_exists = True
    except Exception:
        id = None
        team_exists = False
    if id is None or team_exists == False:
        return render_template('controller_init.html', **globals())
    else:
        return render_template('controller.html', **globals())


@app.route('/register_controller')
def register_controller():
    name = request.args.get("name")
    if name is not None and len(session["teams"]) < 4:
        id = len(session["teams"])
        team_dict = {"id": id,
                     "name": name,
                     "score": 0,
                     "answer": {"question" : -1, "answer": 0}}
        app.logger.info(team_dict)
        session["teams"].append(team_dict)
        return jsonify(response="success",
                       id=id)
    else:
        return jsonify(response="failed")

@app.route('/start_quiz')
def start_quiz():
    session["status"] = "accepting-answers"
    return jsonify(response="success")


def check_answers():
    next_question = True
    for team in session["teams"]:
        app.logger.info(team)
        app.logger.info(session)
        if team["answer"]["question"] != session["cur_question"]:
            next_question = False
    if next_question:
        for team in session['teams']:
            question = questions[session["cur_question"]]
            app.logger.info(question)
            app.logger.info(team)
            if int(team["answer"]["answer"]) == question["correct_answer"]:
                team["score"] += 10
        if session["cur_question"] != len(questions) - 1:
            session["cur_question"] += 1
        else:
            session["status"] = "endgame"



@app.route('/send_answer')
def send_answer():
    answer = request.args.get("answer")
    team_id = int(request.args.get("team_id"))
    if answer is not None and team_id is not None:
        session["teams"][team_id]["answer"]["question"] = session["cur_question"]
        session["teams"][team_id]["answer"]["answer"] = answer
        response = "success"
    else:
        response = "failed"
    check_answers()
    return jsonify(response=response)


@app.route('/session_data')
def session_data():
    #app.logger.info(session)
    return jsonify(session=session, questions=questions, config=config, question=questions[session["cur_question"]])


@app.route('/')
def home():
    if session["status"] != "endgame":
        return render_template('quiz.html', question=questions[session["cur_question"]], **globals())
    else:
        return render_template('endgame.html', **globals())


@app.route('/restart')
def restart():
    return "done"
    sys.exit()

@app.route('/<path:path>')
def static_proxy(path):
  return app.send_static_file(path)


@app.route('/penalty')
def penalty():
    session["teams"][int(request.args.get('id'))]["score"] -= int(request.args.get("amount"))
    return "done"

if __name__ == "__main__":
    app.run(host="0.0.0.0")
