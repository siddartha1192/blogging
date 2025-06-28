from flask import Flask, render_template, request, redirect, url_for, flash, abort, send_from_directory, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import markdown
import os
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-testing')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///techblog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Context processors
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

@app.context_processor
def inject_categories():
    return {'categories': Category.query.all()}

# Define models
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    color = db.Column(db.String(20))
    posts = db.relationship('Post', backref='category', lazy=True)

class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    bio = db.Column(db.Text)
    avatar = db.Column(db.String(200))
    posts = db.relationship('Post', backref='author', lazy=True)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    excerpt = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    publish_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    read_time = db.Column(db.Integer, default=5)
    featured = db.Column(db.Boolean, default=False)
    featured_image = db.Column(db.String(200))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'), nullable=False)
    topics = db.relationship('Topic', secondary='post_topics', backref=db.backref('posts', lazy='dynamic'))

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)

class Subscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    subscribed_on = db.Column(db.DateTime, default=datetime.utcnow)

# Association table for Post and Topic many-to-many relationship
post_topics = db.Table('post_topics',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
    db.Column('topic_id', db.Integer, db.ForeignKey('topic.id'), primary_key=True)
)

def subscribe(request):
    email = request.get('email')
    
    if not email:
        # Return JSON error if it's an AJAX call
        if request.is_json:
            return jsonify({'status': 'danger', 'message': 'Please provide a valid email.'}), 400
        flash('Please provide a valid email.', 'danger')
        return redirect(request.referrer or url_for('home'))
    
    existing = Subscriber.query.filter_by(email=email).first()
    if existing:
        if request.is_json:
            return jsonify({'status': 'warning', 'message': 'You are already subscribed!'}), 200
        flash('You are already subscribed!', 'warning')
    else:
        new_sub = Subscriber(email=email)
        db.session.add(new_sub)
        db.session.commit()
        if request.is_json:
            return jsonify({'status': 'success', 'message': 'Subscription successful!'}), 200
        flash('Subscription successful!', 'success')