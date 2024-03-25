from flask import request, jsonify, Blueprint
from .index import app, db, Event, Presentation, Question, User

admin = Blueprint('admin', __name__, template_folder='templates')

# Route to get all events
@admin.route('/event', methods=['GET'])
def get_events():
    events = Event.query.order_by(Event.date).all()
    return jsonify([{'id': e.id_event, 'name': e.name, 'date': e.date, 'page': e.page} for e in events]), 200

# Route to create or update an event
@admin.route('/event', methods=['POST'])
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
@admin.route('/event', methods=['DELETE'])
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
@admin.route('/presentation', methods=['GET'])
def get_presentations():
    presentations = Presentation.query.order_by(Presentation.datetime_start).all()
    return jsonify([{'id': p.id_presentation, 'name': p.name, 'datetime_start': p.datetime_start, 'duration': p.duration, 'page': p.page, 'event_id': p.event_id} for p in presentations]), 200

# Route to create or update a presentation
@admin.route('/presentation', methods=['POST'])
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
@admin.route('/presentation', methods=['DELETE'])
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
@admin.route('/question', methods=['GET'])
def get_questions():
    questions = Question.query.all()
    return jsonify([{'id': q.id_question, 'content': q.content, 'author_id': q.author_id, 'presentation_id': q.presentation_id} for q in questions]), 200

# Route to create or update a question
@admin.route('/question', methods=['POST'])
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
@admin.route('/question', methods=['DELETE'])
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
@admin.route('/user', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([{'id': u.id_user, 'name': u.name, 'email': u.email, 'public_id': u.public_id, 'bio': u.bio} for u in users]), 200

# Route to create or update a user
@admin.route('/user', methods=['POST'])
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
@admin.route('/user', methods=['DELETE'])
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