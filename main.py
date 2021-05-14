from flask import Flask, render_template, redirect, request, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import secrets
import statistics

app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///formdata.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = 'True'
app.config['SECRET_KEY'] = secrets.token_urlsafe(16)

db = SQLAlchemy(app)


class Formdata(db.Model):
	__tablename__ = 'formdata'
	id = db.Column(db.Integer, primary_key=True)
	created_at = db.Column(db.DateTime, default=datetime.now)
	q1 = db.Column(db.Integer)
	q2 = db.Column(db.Integer)
	q3 = db.Column(db.Integer)

	def __init__(self, q1, q2, q3):		
		self.q1 = q1
		self.q2 = q2
		self.q3 = q3

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



img_list = ['Ishihara_2.svg', 'Ishihara_2.svg', 'Ishihara_2.svg']
possible_answers = [[5, 1, 67, 2],
					[12, 6, 67, 2],
					[2, 1, 12, 2]]

@app.route("/start_test/", methods=['POST'])
def start_test():
	session['answers'] = {
					  "test_1": 0,
					  "test_2": 0,
					  "test_3": 0,
					 }
	
	session['index_add_counter'] = 0
	return redirect("/next_question/")

@app.route("/next_question/", methods=['POST', 'GET'])
def next_question():
	counter = session['index_add_counter']
	if session['index_add_counter']!=0:
		answer = request.form['question']
		session['answers'][f"test_{counter}"] = answer
	session['index_add_counter'] = counter+1

	if counter < len(img_list):
		return redirect("/test")
	else:
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

@app.route("/save/", methods=['POST', 'GET'])
def save():
	# Get data from FORM
	answers = session['answers']
	print(answers)
	q1 = answers['test_1']
	q2 = answers['test_2']
	q3 = answers['test_3']

	# Save the data
	fd = Formdata(q1, q2, q3)
	db.session.add(fd)
	db.session.commit()

	return redirect('/')


if __name__ == "__main__":
	app.debug = True
	app.run()
