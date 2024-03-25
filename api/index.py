from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, redirect, url_for, session, copy_current_request_context
from flask_jwt_extended import create_access_token, verify_jwt_in_request, JWTManager
import json, os
from flask_jwt_extended import create_access_token, verify_jwt_in_request, JWTManager, get_jwt_identity
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from time import time
from flask_cors import CORS
import secrets

db = SQLAlchemy()

# Event model
class Event(db.Model):
    __tablename__ = 'events'
    id_event = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    page = db.Column(db.Text, nullable=False)
    presentations = db.relationship('Presentation', backref='event', lazy=True)
    attendees = db.relationship('User', secondary='user_events', back_populates='attended_events')

# Presentation model
class Presentation(db.Model):
    __tablename__ = 'presentations'
    id_presentation = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    page = db.Column(db.Text, nullable=False)  # Contains HTML
    datetime_start = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # Duration in minutes
    moderatorToken = db.Column(db.String(255), nullable=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id_event'), nullable=False)
    questions = db.relationship('Question', backref='presentation', lazy=True)
    interested_users = db.relationship('User', secondary='user_presentations', back_populates='presentations_to_attend')

# Question model
class Question(db.Model):
    __tablename__ = 'questions'
    id_question = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id_user'))
    author = db.relationship('User', backref='questions', overlaps="author,questions")
    anonymous = db.Column(db.Boolean, nullable=False, default=False)
    archived = db.Column(db.Boolean, nullable=False, default=False)
    presentation_id = db.Column(db.Integer, db.ForeignKey('presentations.id_presentation'), nullable=False)
    liked_by_users = db.relationship('User', secondary='question_likes', back_populates='liked_questions', overlaps="author,questions")


# User model
class User(db.Model):
    __tablename__ = 'users'
    id_user = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)

    one_time_token = db.Column(db.String(255), nullable=True)
    one_time_token_sent = db.Column(db.DateTime, nullable=True)
    one_time_token_tries = db.Column(db.Integer, nullable=True)
    one_time_token_last_try = db.Column(db.DateTime, nullable=True)
    device_token = db.Column(db.String(255), nullable=True)
    public_id = db.Column(db.String(255), nullable=False, unique=True)

    bio = db.Column(db.JSON, nullable=True)
    authored_questions = db.relationship('Question', backref='users', overlaps="author,questions")
    attended_events = db.relationship('Event', secondary='user_events', back_populates='attendees')
    presentations_to_attend = db.relationship('Presentation', secondary='user_presentations', back_populates='interested_users')
    liked_questions = db.relationship('Question', secondary='question_likes', back_populates='liked_by_users', overlaps="author,questions")

# Many-to-many tables
user_events = db.Table('user_events',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id_user'), primary_key=True),
    db.Column('event_id', db.Integer, db.ForeignKey('events.id_event'), primary_key=True)
)

user_presentations = db.Table('user_presentations',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id_user'), primary_key=True),
    db.Column('presentation_id', db.Integer, db.ForeignKey('presentations.id_presentation'), primary_key=True)
)

question_likes = db.Table('question_likes',
    db.Column('question_id', db.Integer, db.ForeignKey('questions.id_question'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id_user'), primary_key=True)
)

template_dir = os.path.abspath('templates')
static_dir = os.path.abspath('static')
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {"pool_pre_ping": True}  
#app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://jak3679:rMJgknGTL20j@ep-soft-mountain-44625884.eu-central-1.aws.neon.tech/neondb"
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:admin@localhost:5432/"
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 1
app.config["JWT_SECRET_KEY"] = "3uv7Pk2Dd7VCX00cJ"
db.init_app(app)
jwt = JWTManager(app)
CORS(app)


deployDateTime = datetime.now()
ipsVisited = set()
ipDetails = {}
@app.route('/')
def home():
    amountOfRequests = app.config.get('AMOUNT_OF_REQUESTS', 0)
    app.config['AMOUNT_OF_REQUESTS'] = amountOfRequests + 1
    ipsVisited.add(request.remote_addr)
    ipDetails[request.remote_addr] = str(request.headers.get('User-Agent'))
    ipsVisitedStr = ''
    for ip in ipsVisited: ipsVisitedStr += "<a href='https://iplocation.io/ip/' target='_blank'" + ip + "'>" + ip + "</a> " + ipDetails[ip] + "<br>"
    return '<body>Batovka#0.1' + '<br>' + deployDateTime.strftime('%Y-%m-%d %H:%M:%S') + '<br>' + str((datetime.now()-deployDateTime)) + '<br>' + str(amountOfRequests) + '<br>' + ipsVisitedStr + '</body>'

@app.route('/favicon.ico')
def favicon(): return app.send_static_file('icon.png')

@app.route('/resetTheDb')
def resetDb():
    db.drop_all()
    db.create_all()
    insertData()
    return 'Ok'

def insertData():
    event = Event(name='Event 1', date=datetime.now(), page='page 1')
    db.session.add(event)
    db.session.commit()
    presentation = Presentation(name='Presentation 1', page='page 1', datetime_start=datetime.now(), duration=60, event_id=event.id_event)
    db.session.add(presentation)
    db.session.commit()
    user = User(name='User 1', email='test@test.test', public_id='user 1')
    db.session.add(user)
    db.session.commit()
    user.attended_events.append(event)
    user.presentations_to_attend.append(presentation)
    db.session.commit()
    question = Question(content='Question 1', author_id=user.id_user, presentation_id=presentation.id_presentation)
    db.session.add(question)
    db.session.commit()
    user.liked_questions.append(question)
    db.session.commit()
    return 'Ok'


# ADMIN ROUTES

from api.admin import admin
app.register_blueprint(admin, url_prefix='/admin')

from api.user import user
app.register_blueprint(user, url_prefix='/user')

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    if user:
        doNotSendNextTokenUntil = datetime.now() + timedelta(minutes=1)
        if user.one_time_token and user.one_time_token_sent and user.one_time_token_sent > doNotSendNextTokenUntil:
            return jsonify({'message': 'One time token already sent, try again in 1 minute'}), 400
        one_time_token = ''.join([str(secrets.randbelow(10)) for i in range(6)])
        user.one_time_token = one_time_token
        user.one_time_token_tries = 0
        user.one_time_token_last_try = None
        user.one_time_token_sent = datetime.now()
        db.session.commit()
        print('One time token for ' + user.email + ' is ' + one_time_token)
        return jsonify({'message': 'One time token sent'}), 200
    else:
        return jsonify({'message': 'Invalid email'}), 401
    
@app.route('/loginCode', methods=['POST'])
def loginCode():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    if not user: return jsonify({'message': 'Invalid user'}), 401
    if user.one_time_token_sent and user.one_time_token_sent < datetime.now() - timedelta(minutes=10):
        user.one_time_token = None
        user.one_time_token_sent = None
        db.session.commit()
        return jsonify({'message': 'Token expired'}), 402
    if user.one_time_token_tries and user.one_time_token_tries > 3:
        user.one_time_token = None
        user.one_time_token_sent = None
        db.session.commit()
        return jsonify({'message': 'Too many tries'}), 403
    if user.one_time_token_last_try and user.one_time_token_last_try > datetime.now() - timedelta(seconds=1):
        return jsonify({'message': 'Too many tries'}), 403
    user.one_time_token_last_try = datetime.now()
    user.one_time_token_tries += 1
    if  user.one_time_token == data['code']:
        user.one_time_token = None
        user.one_time_token_sent = None
        device_token = secrets.token_urlsafe(128)
        user.device_token = device_token
        db.session.commit()
        return jsonify({'access_token': device_token}), 200
    else:
        db.session.commit()
        return jsonify({'message': 'Invalid code'}), 401