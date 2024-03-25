from flask import request, jsonify, Blueprint
from flask_jwt_extended import jwt_required, create_access_token
from .index import app, jwt, db, Question, User

user = Blueprint('user', __name__, template_folder='templates')
    
# Login route
@user.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    if user and data['password'] == user.password:
        access_token = create_access_token(identity=user.public_id)
        return jsonify({'access_token': access_token}), 200
    else:
        return jsonify({'message': 'Invalid email or password'}), 401
    
# Route to create or update the question
@user.route('/question/<presentation_id>', methods=['POST'])
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
@user.route('/question/like/<question_id>', methods=['POST', 'DELETE'])
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
@user.route('/question/<presentation_id>', methods=['GET'])
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
@user.route('/question/<question_id>', methods=['DELETE'])
def delete_question_by_id(question_id):
    id_user = jwt.get_jwt_identity()
    if not id_user: return jsonify({'message': 'User not found'}), 404
    question = Question.query.filter_by(id_question=question_id).first()
    if not question: return jsonify({'message': 'Question not found'}), 404
    if question.author_id != id_user: return jsonify({'message': 'User is not the author of the question'}), 403
    question.archived = True
    db.session.commit()
    return jsonify({'result': 'Ok'}), 200