from datetime import datetime, timezone
from extension import db

# 法院案例
class JudicalCase(db.Model):
    __tablename__ = "judicial_cases"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    keywords = db.Column(db.Text, nullable=True)
    basic_facts = db.Column(db.Text, nullable=True)
    judgment_reasons = db.Column(db.Text, nullable=True)
    judgment_essence = db.Column(db.Text, nullable=True)
    related_indices = db.Column(db.Text, nullable=True)

# 裁判文书


# 法律法规
