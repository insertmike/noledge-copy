from flask import Flask , redirect , render_template, request, url_for, flash, jsonify, g, Response
from flask_mail import Mail, Message
import sqlite3
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.datastructures import ImmutableMultiDict
from flask_login import LoginManager , UserMixin , login_required ,login_user, logout_user,current_user
from secret import mail_server, mail_port, mail_username, mail_password, mail_use_ssl, mail_use_tls
from flask_login import LoginManager
import json
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import load_only
import datetime
from sqlalchemy.sql import func
from sqlalchemy import desc


app=Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///db.db'
app.config['SECRET_KEY'] = '!9m@S-dThyIlW[pHQbN^'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False

mail = Mail(app)
app.config['MAIL_SERVER']=mail_server
app.config['MAIL_PORT'] = mail_port
app.config['MAIL_USERNAME'] = mail_username
app.config['MAIL_PASSWORD'] = mail_password
app.config['MAIL_USE_TLS'] = mail_use_tls
app.config['MAIL_USE_SSL'] = mail_use_ssl
mail = Mail(app)

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def get_user(user_id):
    return User.query.get(user_id)


class AlchemyEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            # an SQLAlchemy class
            fields = {}
            for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                data = obj.__getattribute__(field)
                try:
                    json.dumps(data) # this will fail on non-encodable values, like other classes
                    fields[field] = data
                except TypeError:
                    fields[field] = None
            # a json-encodable dict
            return fields

        return json.JSONEncoder.default(self, obj)

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String(80))
    name = db.Column(db.String(80))
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __init__(self, password, name, email):
        self.password = generate_password_hash(password)
        self.name = name
        self.email = email

    def __repr__(self):
        return f'<User {self.name}>'

    def verify_password(self, pwd):
        return check_password_hash(self.password, pwd)

class Test(db.Model, UserMixin):
    __tablename__ = 'test'
    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'),  nullable=False)
    name = db.Column(db.String(80),  nullable=False)

    def __init__(self, creator_id, name):
        self.creator_id = creator_id
        self.name = name

    def __repr__(self):
        return f'<Test {self.name}>'

class Question(db.Model, UserMixin):
    __tablename__ = 'question'
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(80),  nullable=False)
    test_id = db.Column(db.Integer,   db.ForeignKey('test.id'),  nullable=False)

    def __init__(self, question, test_id):
        self.question = question
        self.test_id = test_id

    def __repr__(self):
        return f'<Question {self.question}>'

class Answer(db.Model, UserMixin):
    __tablename__ = 'answer'
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'),  nullable=False)
    answer = db.Column(db.String(80),  nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)

    def __init__(self, question_id, answer, is_correct):
        self.question_id = question_id
        self.answer = answer
        self.is_correct = is_correct

    def getIsCorrect(self):
        return is_correct

    def __repr__(self):
        return f'<Answer {self.answer}>'

class TestAttempt(db.Model, UserMixin):
    __tablename__ = 'testattempt'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),  nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey('test.id'),  nullable=False)
    score = db.Column(db.Integer,  nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.datetime.now)

    def __init__(self, user_id,test_id,score):
        self.user_id = user_id
        self.test_id = test_id
        self.score = score

    def __repr__(self):
        return f'<TestAttempt {self.id}>'

@app.route('/submitTest', methods=['POST'])
def submit_test():
    print(current_user)
    if not current_user.is_authenticated:
        return Response("Error", status=400, mimetype='application/json')
    if not request.form:
        return Response("Error", status=400)
    data = request.form.to_dict()
    data = json.loads((list(data.keys())[0]))
    if(len(data['questions']) < 1 or len(data['questions']) > 5):
        return Response("Error", status=400)
    test = Test(current_user.get_id(),data['name'])
    db.session.add(test)
    db.session.commit()
    # TEST ID
    test_id = int(test.get_id())
    # ADD QUESTION -> ANSWERS
    for curr in data['questions']:
        # ADD QUESTION
        question = curr['question']
        currQuestion = Question(question,test_id)
        db.session.add(currQuestion)
        db.session.commit()
        question_id = currQuestion.get_id()
        # ADD ANSWERS
        correct = curr['correct']
        wrong1 = curr['wrong1']
        wrong2 = curr['wrong2']
        wrong3 = curr['wrong3']
        correctAnswer = Answer(question_id,correct,True)
        wrong1 = Answer(question_id,wrong1,False)
        wrong2 = Answer(question_id,wrong2,False)
        wrong3 = Answer(question_id,wrong3,False)
        db.session.add(correctAnswer)
        db.session.add(wrong1)
        db.session.add(wrong2)
        db.session.add(wrong3)
        db.session.commit()
        print('Added question:', question_id)
    return Response("Success", status=200)

@app.route('/submitForm', methods=['POST'])
def submit_form():

    if not request.form:
        return "Email failed to send"

    email    = request.form['email']
    name = request.form['fullname']
    message  = request.form['subject']

    if not email or not name or not message:
        return "Email failed to send"

    msg = Message(
                'Hello',
                sender = mail_username,
                recipients = ['mikeionchew@gmail.com']
                 )
    msg.body = 'Message from: ' + name + ' with email: ' + email + ' sends you the following message:' + message
    try:
        mail.send(msg)
        return "Email sent"
    except:
        return "Email failed to send"

@app.route('/newTest',methods=['GET'])
def new_test():
    print(current_user.is_authenticated)
    if not current_user.is_authenticated:
        return render_template('landing.html')
    else:
        return render_template('create.html')

@app.route('/browse',methods=['GET'])
def get_browse():
    if not current_user.is_authenticated:
        return render_template('landing.html')
    return render_template('browse.html')

@app.route('/solve/<int:test_id>', methods=['GET', 'POST'])
def solveTest(test_id):
    if not current_user.is_authenticated:
            return Response("Error", status=400)
    if request.method == 'GET':
        test = db.session.query(Test, Question, Answer).with_entities(Test.id, Test.name,Question.question, Question.id, Answer.answer).filter(Test.id==test_id).filter(Test.id==Question.test_id).filter(Answer.question_id == Question.id).all()
        return render_template('solve.html', solve_test= json.dumps(test, cls=AlchemyEncoder))
    if request.method == 'POST':
        if not request.form:
            return Response("Error", status=400)
        data = request.form.to_dict()
        keys = list(data.keys())
        if not keys:
            return 0
        score = 0
        for key in keys:
            res = db.session.query(Answer).filter(Answer.question_id == key).filter(Answer.answer == data[key]).filter(Answer.is_correct == True).all()
            if res:
                score += 1
        testAttempt = TestAttempt(current_user.get_id(), test_id, score)
        db.session.add(testAttempt)
        db.session.commit()
        return str(score)

@app.route('/test',methods=['GET'])
def get_tests():
    if not current_user.is_authenticated:
        return Response("Error", status=400, mimetype='application/json')
    tests = db.session.query(Test, User).with_entities(Test.id,Test.name, User.name).filter(Test.creator_id == User.id).all()
    #query_db('SELECT test.name, user.name FROM test INNER JOIN test ON test.creator_id = user.id')
    print(tests)
    return json.dumps(tests, cls=AlchemyEncoder)

@app.route('/',methods=['GET'])
def get_home():
    if current_user.is_authenticated:
        print(current_user.password)
        print(current_user.email)
        res = db.session.query(func.sum(TestAttempt.score)).filter(TestAttempt.user_id == current_user.get_id()).all()
        points = '0'
        if res[0][0]:
            points = str(res[0][0])
        res = db.session.query(TestAttempt).filter(TestAttempt.user_id == current_user.get_id()).all()
        testAttempts = str(len(res))
        if not testAttempts:
            testAttemps = '0'
        res = db.session.query(Test).filter(Test.creator_id == current_user.get_id()).all()
        createdTests = str(len(res))
        if not createdTests:
            createdTests = '0'
        res = db.session.query(Test).all()
        total_tests = str(len(res))
        if not total_tests:
            total_tests = '0'
        res = db.session.query(User).all()
        total_users = str(len(res))
        if not total_users:
            total_users = '0'
        res = db.session.query(TestAttempt.score).filter(TestAttempt.user_id == current_user.get_id()).order_by(TestAttempt.score.desc()).limit(3).all()
        top_3 = []
        res = json.dumps(res, cls=AlchemyEncoder)
        res = json.loads(res)
        print(res)
        for score in res:
            top_3.append(score)
        if not len(top_3):
            top_3 = []
        print(top_3)
        return render_template('home.html', top_3 = top_3,points=points, totalUsers=total_users, testAttempts=testAttempts, total_tests=total_tests, createdTests=createdTests)
    else:
        return render_template('landing.html')

@login_manager.unauthorized_handler     # In unauthorized_handler we have a callback URL
def unauthorized_callback():            # In call back url we can specify where we want to
       return redirect(url_for('get_login')) # redirect the user in my case it is login page!

@app.route('/landing',methods=['GET'])
def get_landing():
    return render_template('landing.html')

@app.route('/login',methods=['GET'])
def get_login():
    if current_user.is_authenticated:
        print(current_user.password)
        print(current_user.email)
        return render_template('home.html')
    return render_template('login.html')

@app.route('/signup',methods=['GET'])
def get_signup():
    return render_template('signup.html')

@app.route('/login',methods=['POST'])
def login_post():
    if current_user.is_authenticated:
        print(current_user.password)
        print(current_user.email)
        return render_template('home.html')
    email = request.form['email']
    password = request.form['password']
    user = User.query.filter_by(email=email).first()

    if user and user.verify_password(password):
        login_user(user)
        flash("User logged-in!")
        return redirect('/')
    else:
        flash("Invalid login!")
        return redirect('/login')

@app.route('/register',methods=['POST'])
def signup_post():
    email = request.form['regemail']
    password = request.form['regpassword']
    name = request.form['name']
    if not email or not password or not name:
        flash('Already Registered')
        return redirect('/login')
    user = User.query.filter_by(email=email).first()
    if user:
        return redirect('/login')
    user = User(email=email,password=password, name=name)
    db.session.add(user)
    db.session.commit()
    user = User.query.filter_by(email=email).first()
    if not user:
        return redirect('/login')
    login_user(user)
    return redirect('/')


@app.route('/logout',methods=['GET'])
def logout():
    logout_user()
    return redirect('/login')





if __name__=='__main__':
    db.create_all()
    app.run(debug=True)