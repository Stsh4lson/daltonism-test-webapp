from flask import Flask, render_template, redirect, request, url_for, session,Response
from flask import globals as g
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime
import numpy as np
import secrets
import statistics
import io
import random
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///formdata.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = 'True'
app.config['SECRET_KEY'] = secrets.token_urlsafe(16)

db = SQLAlchemy(app)

g.start = None

class Formdata(db.Model):
    __tablename__ = 'formdata'
    id = db.Column(db.Integer, primary_key=True)
    # created_at = db.Column(db.DateTime, default=datetime.now)
    unique_user_id = db.Column(db.Text)
    no_task = db.Column(db.Integer)
    solved = db.Column(db.Integer)
    time = db.Column(db.Integer)

    def __init__(self, unique_user_id, no_task, solved, time):
        self.unique_user_id = unique_user_id
        self.no_task = no_task
        self.solved = solved
        self.time = time

db.create_all()


@app.route("/")
def welcome():
    return render_template('welcome.html')

@app.route("/form")
def show_form():
    return render_template('form.html')

@app.route("/raw")
def show_raw():
    fd = db.session.query(Formdata).all()
    return render_template('raw.html', formdata=fd)


img_list = ['4.3.png', '4.png', '1.3.png', '6.9.png', '1.7.png', '7.png', '4.6.png', '4.2.png', '4.8.png', '6.11.png', '1.5.png', '4.7.png', '1.3.png', '1.5.png', '4.7.png']
possible_answers = [[1, 2, 4, 7],
                    [2, 4, 8, 9],
                    [1, 3, 4, 7],
                    [2, 5, 6, 9],
                    [1, 4, 7, 8],
                    [1, 3, 4, 7],
                    [2, 4, 6, 8],
                    [3, 4, 5, 7],
                    [2, 4, 6, 8],
                    [1, 3, 6, 9],
                    [1, 4, 5, 6],
                    [1, 4, 6, 8],
                    [1, 4, 6, 9],
                    [1, 3, 7, 8],
                    [4, 7, 8, 9]]

@app.route("/start_test/", methods=['POST'])
def start_test():
    
    session['unique_user_id'] = secrets.token_hex(nbytes=16)
    
    session['answers'] = {}
    for i in range(0, len(img_list)):
        session['answers'][f'test_{i+1}'] = 0
 
    # initializing time dictionary
    session['time'] = {}
    for i in range(0, len(img_list)):
        session['time'][f'time_{i+1}'] = 0
  
    session['index_add_counter'] = 0
    return redirect("/next_question/")

@app.route("/next_question/", methods=['POST', 'GET'])
def next_question():
    if g.start == None:
        g.start = datetime.now()
    
    counter = session['index_add_counter']
    if session['index_add_counter']!=0:
        answer = request.form['question']
        print(answer)
        session['answers'][f"test_{counter}"] = answer
        #calculating elapsed time 
        time = datetime.now() - g.start
        session['time'][f"time_{counter}"] = time.total_seconds()
        g.start = datetime.now()
    session['index_add_counter'] = counter+1

    if counter < len(img_list):
        return redirect("/test")
    else:
        g.start = None
        return redirect("/plot/")
        

@app.route("/test")
def do_testing():
    counter = session['index_add_counter']
    questions = possible_answers[counter-1]
    return render_template('test.html',
                            img_name=img_list[counter-1],
                            answer_1=questions[0],
                            answer_2=questions[1],
                            answer_3=questions[2],
                            answer_4=questions[3]
                           )

@app.route("/info")
def do_info():	
    return render_template('info.html')

@app.route('/plot/')
def plot_png():
    fig = create_figure()
    plt.savefig("static\graphs\disp.png")
    return  redirect('/display_results')

@app.route('/display_results')
def display_png():

    return render_template('display_results.html')


def create_figure():
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    xs = range(100)
    ys = [random.randint(1, 50) for x in xs]
    axis.plot(xs, ys)
    return fig

@app.route("/save/", methods=['POST', 'GET'])
def save():
    # Get data from FORM
    
    no_task = range(1, len(img_list)+1)
    unique_user_id = session['unique_user_id']
    answers = session['answers']
    time = session['time']
    print(no_task)
    for i in range(len(answers)):
        fd = Formdata(unique_user_id,
                      no_task[i],
                      answers[f"test_{i+1}"],
                      time[f"time_{i+1}"])
        db.session.add(fd)
    db.session.commit()

    return redirect('/')


if __name__ == "__main__":
    app.debug = True
    app.run()
