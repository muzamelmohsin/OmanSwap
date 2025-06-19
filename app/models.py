from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text)
    phone_number = db.Column(db.String(20), nullable=False)
    province = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='user')

    posts = db.relationship('Post', backref='owner', lazy=True)
    exchange_requests_sent = db.relationship('ExchangeRequest', backref='proposer', lazy=True)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        return f'<Category {self.name}>'

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    province = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    image = db.Column(db.String(200))
    status = db.Column(db.String(50), default='available')  # 'available' or 'accepted'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    exchange_requests_received = db.relationship(
        'ExchangeRequest',
        foreign_keys='ExchangeRequest.target_post_id',
        lazy=True
    )

class ExchangeRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    proposer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    proposer_post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    target_post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    message = db.Column(db.Text)
    is_accepted = db.Column(db.Boolean, default=False)
    is_rejected = db.Column(db.Boolean, default=False)

    proposer_post = db.relationship('Post', foreign_keys=[proposer_post_id])
    target_post = db.relationship('Post', foreign_keys=[target_post_id])
