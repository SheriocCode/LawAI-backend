from extension import db
from flask_cors import CORS

def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()

def cors(app):
    CORS(app, resources={r"/*": {"origins": "*"}})