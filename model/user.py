from datetime import datetime, timezone
from extension import db

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    avatar = db.Column(db.String(100), nullable=True)
    signature = db.Column(db.String(200), nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    register_date = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))

class BrowseHistory(db.Model):
    __tablename__ = "browse_histories"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class Collect(db.Model):
    __tablename__ = "collects"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    doc_id = db.Column(db.Integer, nullable=False)
    doc_type = db.Column(db.String(50), nullable=False)
    collect_date = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
