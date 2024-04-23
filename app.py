from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Configuration for JWT
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'super-secret')
jwt = JWTManager(app)

# Configuration for SQLAlchemy
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Model for articles
class Articles(db.Model):
    __tablename__ = 'Articles'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(25))
    body = db.Column(db.String(25))
    date = db.Column(db.DateTime, default=db.func.current_timestamp())

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'body': self.body,
            'date': self.date.strftime('%Y-%m-%d %H:%M:%S')
        }

# Model for users
class User(db.Model):
    __tablename__ = 'Users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(255))

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username
        }

# Model for blogs
class Blog(db.Model):
    __tablename__ = 'Blogs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'))
    user = db.relationship('User', backref=db.backref('blogs', lazy=True))
    content = db.Column(db.String(255))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'content': self.content
        }

# Routes for articles
@app.route('/articles', methods=['GET'])
def get_articles():
    all_articles = Articles.query.all()
    articles_data = [article.to_dict() for article in all_articles]
    return jsonify(articles_data)

@app.route('/articles/<int:id>', methods=['GET'])
def get_article(id):
    article = Articles.query.get(id)
    if not article:
        return jsonify({'error': 'Article not found'}), 404
    return jsonify(article.to_dict())

@app.route('/articles', methods=['POST'])
@jwt_required()
def add_article():
    data = request.get_json()
    title = data.get('title')
    body = data.get('body')

    article = Articles(title=title, body=body)
    db.session.add(article)
    db.session.commit()
    return jsonify(article.to_dict()), 201

@app.route('/articles/<int:id>', methods=['PUT'])
@jwt_required()
def update_article(id):
    article = Articles.query.get(id)
    if not article:
        return jsonify({'error': 'Article not found'}), 404
    data = request.get_json()
    article.title = data.get('title', article.title)
    article.body = data.get('body', article.body)
    db.session.commit()
    return jsonify(article.to_dict())

@app.route('/articles/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_article(id):
    article = Articles.query.get(id)
    if not article:
        return jsonify({'error': 'Article not found'}), 404
    db.session.delete(article)
    db.session.commit()
    return jsonify(article.to_dict())

# User authentication
@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    user = User.query.filter_by(username=username, password=password).first()
    if not user:
        return jsonify({"message": "Invalid credentials"}), 401
    access_token = create_access_token(identity=username)
    return jsonify({"token": access_token}), 200

@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    username = get_jwt_identity()
    return jsonify(logged_in_as=username), 200

# Routes for profile and blogs
@app.route('/profile', methods=['POST'])
@jwt_required()
def save_profile():
    data = request.get_json()
    username = data.get('username')
    image = data.get('image')
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400
    new_user = User(username=username, image=image)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'id': new_user.id, 'username': username, 'image': image}), 201

@app.route('/blogs', methods=['GET'])
def get_blogs():
    all_blogs = Blog.query.all()
    blog_data = [{'id': blog.id, 'user_id': blog.user_id, 'content': blog.content} for blog in all_blogs]
    return jsonify(blog_data)

@app.route('/blogs', methods=['POST'])
@jwt_required()
def add_blog():
    data = request.get_json()
    user_id = data.get('user_id')
    content = data.get('content')
    new_blog = Blog(user_id=user_id, content=content)
    db.session.add(new_blog)
    db.session.commit()
    return jsonify({'id': new_blog.id, 'user_id': user_id, 'content': content}), 201

if __name__ == '__main__':
    app.run(debug=True)
