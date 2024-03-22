from flask import Flask, render_template, jsonify, request, redirect, url_for, session, copy_current_request_context
from flask_jwt_extended import create_access_token, verify_jwt_in_request, JWTManager
import json, os
from flask_jwt_extended import create_access_token, verify_jwt_in_request, JWTManager, get_jwt_identity
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from time import time
from flask_cors import CORS

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
    event_id = db.Column(db.Integer, db.ForeignKey('events.id_event'), nullable=False)
    questions = db.relationship('Question', backref='presentation', lazy=True)
    interested_users = db.relationship('User', secondary='user_presentations', back_populates='presentations_to_attend')

# Question model
class Question(db.Model):
    __tablename__ = 'questions'
    id_question = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id_user'))
    author = db.relationship('User', backref='questions')
    anonymous = db.Column(db.Boolean, nullable=False, default=False)
    archived = db.Column(db.Boolean, nullable=False, default=False)
    presentation_id = db.Column(db.Integer, db.ForeignKey('presentations.id_presentation'), nullable=False)
    liked_by_users = db.relationship('User', secondary='question_likes', back_populates='liked_questions')

# User model
class User(db.Model):
    __tablename__ = 'users'
    id_user = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=True)
    public_id = db.Column(db.String(255), nullable=False, unique=True)
    bio = db.Column(db.JSON, nullable=True)
    authored_questions = db.relationship('Question', backref='users')
    attended_events = db.relationship('Event', secondary='user_events', back_populates='attendees')
    presentations_to_attend = db.relationship('Presentation', secondary='user_presentations', back_populates='interested_users')
    liked_questions = db.relationship('Question', secondary='question_likes', back_populates='liked_by_users')

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
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://jak3679:rMJgknGTL20j@ep-soft-mountain-44625884.eu-central-1.aws.neon.tech/neondb"
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 1
app.config["JWT_SECRET_KEY"] = "3uv7Pk2Dd7VCX00cJ"
db.init_app(app)
jwt = JWTManager(app)
CORS(app)


deployDateTime = datetime.now()
@app.route('/')
def home():
    amountOfRequests = app.config.get('AMOUNT_OF_REQUESTS', 0)
    app.config['AMOUNT_OF_REQUESTS'] = amountOfRequests + 1
    return 'Batovka#0.1' + '<br>' + deployDateTime.strftime('%Y-%m-%d %H:%M:%S') + '<br>' + str((datetime.now()-deployDateTime)) + '<br>' + str(amountOfRequests)

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
    user = User(name='User 1', email='user 1', public_id='user 1')
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

# Route to get all events
@app.route('/admin/event', methods=['GET'])
def get_events():
    events = Event.query.order_by(Event.date).all()
    return jsonify([{'id': e.id_event, 'name': e.name, 'date': e.date, 'page': e.page} for e in events]), 200

# Route to create or update an event
@app.route('/admin/event', methods=['POST'])
def create_or_update_event():
    data = request.json
    event_id = data.get('id')
    if event_id:
        event = Event.query.filter_by(id_event=event_id).first()
        if event:
            event.name = data.get('name', event.name)
            event.date = data.get('date', event.date)
            event.page = data.get('page', event.page)
        else:
            return jsonify({'message': 'Event not found'}), 404
    else:
        event = Event(name=data['name'], date=data['date'], page=data['page'])
        db.session.add(event)
    db.session.commit()
    return jsonify({'id': event.id_event, 'name': event.name, 'date': event.date, 'page': event.page}), 200

# Route to delete an event
@app.route('/admin/event', methods=['DELETE'])
def delete_event():
    data = request.json
    event_id = data.get('id')
    event = Event.query.filter_by(id_event=event_id).first()
    if event:
        db.session.delete(event)
        db.session.commit()
        return jsonify({'message': 'Event deleted successfully'}), 200
    else:
        return jsonify({'message': 'Event not found'}), 404
    
# Route to get all presentations
@app.route('/admin/presentation', methods=['GET'])
def get_presentations():
    presentations = Presentation.query.order_by(Presentation.datetime_start).all()
    return jsonify([{'id': p.id_presentation, 'name': p.name, 'datetime_start': p.datetime_start, 'duration': p.duration, 'page': p.page, 'event_id': p.event_id} for p in presentations]), 200

# Route to create or update a presentation
@app.route('/admin/presentation', methods=['POST'])
def create_or_update_presentation():
    data = request.json
    presentation_id = data.get('id')
    if presentation_id:
        presentation = Presentation.query.filter_by(id_presentation=presentation_id).first()
        if presentation:
            presentation.name = data.get('name', presentation.name)
            presentation.datetime_start = data.get('datetime_start', presentation.datetime_start)
            presentation.duration = data.get('duration', presentation.duration)
            presentation.page = data.get('page', presentation.page)
            presentation.event_id = data.get('event_id', presentation.event_id)
        else:
            return jsonify({'message': 'Presentation not found'}), 404
    else:
        presentation = Presentation(name=data['name'], datetime_start=data['datetime_start'], duration=data['duration'], page=data['page'], event_id=data['event_id'])
        db.session.add(presentation)
    db.session.commit()
    return jsonify({'id': presentation.id_presentation, 'name': presentation.name, 'datetime_start': presentation.datetime_start, 'duration': presentation.duration, 'page': presentation.page, 'event_id': presentation.event_id}), 200

# Route to delete a presentation
@app.route('/admin/presentation', methods=['DELETE'])
def delete_presentation():
    data = request.json
    presentation_id = data.get('id')
    presentation = Presentation.query.filter_by(id_presentation=presentation_id).first()
    if presentation:
        db.session.delete(presentation)
        db.session.commit()
        return jsonify({'message': 'Presentation deleted successfully'}), 200
    else:
        return jsonify({'message': 'Presentation not found'}), 404
    
# Route to get all questions
@app.route('/admin/question', methods=['GET'])
def get_questions():
    questions = Question.query.all()
    return jsonify([{'id': q.id_question, 'content': q.content, 'author_id': q.author_id, 'presentation_id': q.presentation_id} for q in questions]), 200

# Route to create or update a question
@app.route('/admin/question', methods=['POST'])
def create_or_update_question():
    data = request.json
    question_id = data.get('id')
    if question_id:
        question = Question.query.filter_by(id_question=question_id).first()
        if question:
            question.content = data.get('content', question.content)
            question.author_id = data.get('author_id', question.author_id)
            question.presentation_id = data.get('presentation_id', question.presentation_id)
        else:
            return jsonify({'message': 'Question not found'}), 404
    else:
        question = Question(content=data['content'], author_id=data['author_id'], presentation_id=data['presentation_id'])
        db.session.add(question)
    db.session.commit()
    return jsonify({'id': question.id_question, 'content': question.content, 'author_id': question.author_id, 'presentation_id': question.presentation_id}), 200

# Route to delete a question
@app.route('/admin/question', methods=['DELETE'])
def delete_question():
    data = request.json
    question_id = data.get('id')
    question = Question.query.filter_by(id_question=question_id).first()
    if question:
        db.session.delete(question)
        db.session.commit()
        return jsonify({'message': 'Question deleted successfully'}), 200
    else:
        return jsonify({'message': 'Question not found'}), 404

# Route to get all users
@app.route('/admin/user', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([{'id': u.id_user, 'name': u.name, 'email': u.email, 'public_id': u.public_id, 'bio': u.bio} for u in users]), 200

# Route to create or update a user
@app.route('/admin/user', methods=['POST'])
def create_or_update_user():
    data = request.json
    user_id = data.get('id')
    if user_id:
        user = User.query.filter_by(id_user=user_id).first()
        if user:
            user.name = data.get('name', user.name)
            user.email = data.get('email', user.email)
            user.public_id = data.get('public_id', user.public_id)
            user.bio = data.get('bio', user.bio)
        else:
            return jsonify({'message': 'User not found'}), 404
    else:
        user = User(name=data['name'], email=data['email'], public_id=data['public_id'], bio=data['bio'])
        db.session.add(user)
    db.session.commit()
    return jsonify({'id': user.id_user, 'name': user.name, 'email': user.email, 'public_id': user.public_id, 'bio': user.bio}), 200

# Route to delete a user
def delete_user():
    data = request.json
    user_id = data.get('id')
    user = User.query.filter_by(id_user=user_id).first()
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'}), 200
    else:
        return jsonify({'message': 'User not found'}), 404

# USER ROUTES
    
# Login route
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    if user and data['password'] == user.password:
        access_token = create_access_token(identity=user.public_id)
        return jsonify({'access_token': access_token}), 200
    else:
        return jsonify({'message': 'Invalid email or password'}), 401
    
# Route to create or update the question
@app.route('/question/<presentation_id>', methods=['POST'])
def create_question(presentation_id):
    data = request.json
    id_user = jwt.get_jwt_identity()
    if not id_user: return jsonify({'message': 'User not found'}), 404
    # Check for existing question
    question = Question.query.filter_by(content=data['content'], author_id=id_user, presentation_id=presentation_id).first()
    if question:
        if question.archived: return jsonify({'message': 'Question is archived'}), 400
        question.content = data['content']
        db.session.commit()
        return jsonify({'id': question.id_question, 'content': question.content, 'author_id': question.author_id, 'presentation_id': question.presentation_id}), 200
    question = Question(content=data['content'], author_id=id_user, presentation_id=presentation_id)
    # Check if the content is empty
    if question.content == '': return jsonify({'message': 'Content is empty'}), 400
    db.session.add(question)
    db.session.commit()
    return jsonify({'id': question.id_question, 'content': question.content, 'author_id': question.author_id, 'presentation_id': question.presentation_id}), 200

# Route to like a question
@app.route('/question/like/<question_id>', methods=['POST', 'DELETE'])
def like_question(question_id):
    id_user = jwt.get_jwt_identity()
    if not id_user: return jsonify({'message': 'User not found'}), 404
    question = Question.query.filter_by(id_question=question_id).first()
    if not question: return jsonify({'message': 'Question not found'}), 404
    if question.archived: return jsonify({'message': 'Question is archived'}), 400
    user = User.query.filter_by(public_id=id_user).first()
    if not user: return jsonify({'message': 'User not found'}), 404
    if request.method == 'POST':
        user.liked_questions.append(question)
    else:
        user.liked_questions.remove(question)
    db.session.commit()
    return jsonify({'result': 'Ok'}), 200

# Route to get all questions
@app.route('/question/<presentation_id>', methods=['GET'])
def get_questions_by_presentation(presentation_id):
    #id_user = get_jwt_identity()
    id_user = 1
    questions = Question.query.join(User, Question.author_id == User.id_user).filter(Question.presentation_id == presentation_id, Question.archived == False).all()
    result = []
    for q in questions:
        likes_count = len(q.liked_by_users)
        author_name = 'Anonymous' if q.anonymous else q.author.name
        my_question = q.author_id == id_user
        liked_by_me = id_user in [user.public_id for user in q.liked_by_users]
        result.append({'id': q.id_question, 'content': q.content, 'my_question': my_question, 'likesCount': likes_count, 'authorName': author_name, 'likedByMe': liked_by_me})
    return jsonify(result), 200

# Delete a question
@app.route('/question/<question_id>', methods=['DELETE'])
def delete_question_by_id(question_id):
    id_user = jwt.get_jwt_identity()
    if not id_user: return jsonify({'message': 'User not found'}), 404
    question = Question.query.filter_by(id_question=question_id).first()
    if not question: return jsonify({'message': 'Question not found'}), 404
    if question.author_id != id_user: return jsonify({'message': 'User is not the author of the question'}), 403
    question.archived = True
    db.session.commit()
    return jsonify({'result': 'Ok'}), 200