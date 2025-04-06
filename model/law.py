from datetime import datetime, timezone
from extension import db

# 法院案例
class JudicalCase(db.Model):
    __tablename__ = "judicial_cases"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    keywords = db.Column(db.Text, nullable=True) # 关键词
    basic_facts = db.Column(db.Text, nullable=True) # 基本案情
    judgment_reasons = db.Column(db.Text, nullable=True) # 裁判理由
    judgment_essence = db.Column(db.Text, nullable=True) # 裁判要旨
    related_laws = db.Column(db.Text, nullable=True) # 关联索引-关联法条
    related_trial = db.Column(db.Text, nullable=True) # 关联索引-关联审判程序

# 裁判文书
class JudgmentDocument(db.Model):
    __tablename__ = "judgment_documents"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    trial_court = db.Column(db.String(255), nullable=True) # 审理法院
    document_type = db.Column(db.String(255), nullable=True) # 案件类型
    cause = db.Column(db.Text, nullable=True) # 案由
    trial_procedure = db.Column(db.String(255), nullable=True) # 审判程序
    judgment_date = db.Column(db.Text, nullable=True) # 裁判日期
    client = db.Column(db.Text, nullable=True) # 当事人
    law_basis = db.Column(db.Text, nullable=True) # 法律依据
    category = db.Column(db.Text, nullable=True) # 类别
    decision_num = db.Column(db.Text, nullable=True) # 判决依据
    details = db.Column(db.Text, nullable=True) # 判决内容



# 法律法规
# class Law(db.Model):
#     __tablename__ = "laws"
#     id = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     title = db.Column(db.String(255), nullable=False)
#     content = db.Column(db.Text, nullable=False)
#     category = db.Column(db.Text, nullable=True) # 类别(宪法及相关法)

