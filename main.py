#%%
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
import pandas as pd
from os import environ, name
from sqlalchemy import create_engine
import json
import plotly
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go


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
    correct_answer = db.Column(db.Integer)
    solved = db.Column(db.Integer)
    time = db.Column(db.Integer)
    is_correct = db.Column(db.Boolean)

    def __init__(self, unique_user_id, no_task,correct_answer, solved, time, is_correct):
        
        self.unique_user_id = unique_user_id
        self.no_task = no_task
        self.correct_answer = correct_answer
        self.solved = solved
        self.time = time
        self.is_correct = is_correct

db.create_all()

db_uri = app.config['SQLALCHEMY_DATABASE_URI']
engine = create_engine(db_uri, echo=True)

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
correct_answers = [4, 4, 1, 6, 1, 7, 4, 4, 4 ,6 ,1, 4, 1, 1, 4]

@app.route("/start_test/", methods=['POST'])
def start_test():
    
    session['unique_user_id'] = secrets.token_hex(nbytes=16)
    database_df = pd.read_sql('SELECT unique_user_id FROM formdata', con=engine, coerce_float=True)
    while database_df[database_df['unique_user_id']==session['unique_user_id']].shape[0]>0:
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
        return redirect("/save/")
        

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


@app.route("/save/", methods=['POST', 'GET'])
def save():
    # Get data from FORM
    
    no_task = range(1, len(img_list)+1)
    unique_user_id = session['unique_user_id']
    answers = session['answers']
    time = session['time']

    answ_arr = np.array([*answers.values()]).astype(np.int)
    bool_Arr = np.equal(answ_arr, correct_answers)

    for i in range(len(answers)):
        fd = Formdata(unique_user_id,
                      no_task[i],
                      correct_answers[i],
                      answers[f"test_{i+1}"],
                      time[f"time_{i+1}"],
                      bool_Arr[i]
                      )
        db.session.add(fd)
    db.session.commit()


    return redirect('/display_results')
    
@app.route('/display_results', methods=['POST', 'GET'])
def display():

    unique_user_id = session['unique_user_id']
    table_df = pd.read_sql('SELECT * FROM formdata', con=engine, coerce_float=True)

    table_df_filtered_true = table_df[(table_df["unique_user_id"]  ==  unique_user_id) & (table_df["is_correct"] == 1)]
    table_df_filtered_false = table_df[(table_df["unique_user_id"]  ==  unique_user_id) & (table_df["is_correct"] == 0)]
    table_df_rest_true = table_df[(table_df["unique_user_id"] !=  unique_user_id) & (table_df["is_correct"] == 1)]
    table_df_rest_false = table_df[(table_df["unique_user_id"]  !=  unique_user_id) & (table_df["is_correct"] == 0)]

    fig = make_subplots(rows=3, cols=1, vertical_spacing=0.05,subplot_titles=("Your answers", "Violin plots of your correct vs false answers", "Violin plots of other participants correct vs false answers"))

    fig.add_trace(go.Scatter(x = table_df_filtered_true["no_task"], y=table_df_filtered_true["time"],  name="Correct answers", mode='markers',
            marker=dict(
            color='LightSkyBlue',
            size=20,
            line=dict(
                color='darkslateblue',
                width=2
            ))), row=1, col=1)

    fig.add_trace(go.Scatter(x = table_df_filtered_false["no_task"], y=table_df_filtered_false["time"],  name="False answers", mode='markers',        marker=dict(
            color='darksalmon',
            size=20,
            line=dict(
                color='plum',
                width=2
            ))), row=1, col=1 )

    fig.add_trace(go.Violin(y=table_df_filtered_true["time"],  name="Correct answers",fillcolor='lightblue',line_color='blue'), row=2, col=1 )
    fig.add_trace(go.Violin(y=table_df_filtered_false["time"],  name="False answers",fillcolor='tomato',line_color='red'), row=2, col=1 )

    fig.add_trace(go.Violin(y=table_df_rest_true["time"],  name="Correct answers",fillcolor='slateblue',line_color='steelblue'), row=3, col=1 )
    fig.add_trace(go.Violin(y=table_df_rest_false["time"],  name="False answers",fillcolor='salmon',line_color='darkred'), row=3, col=1 )

    fig.update_layout(autosize=False, width=1000, height=2000,template='ggplot2')
    fig.update_yaxes(automargin=True)

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('display_results.html',graphJSON=graphJSON)

if __name__ == "__main__":
    app.debug = True
    app.run()

# %%
