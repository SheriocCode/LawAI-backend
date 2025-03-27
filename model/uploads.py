from datetime import datetime, timezone
from extension import db

class UploadFile(db.Model):
    __tablename__ = "upload_files"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    file_url = db.Column(db.String(100), nullable=False)
    file_name = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))

class UploadPic(db.Model):
    __tablename__ = "upload_pics"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    pic_url = db.Column(db.String(100), nullable=False)
    pic_name = db.Column(db.String(50))
    ocr_msg = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    