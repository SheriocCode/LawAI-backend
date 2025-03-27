# db.py
from flask import current_app
import traceback
from extension import db
from model.ai import ApiSession, Question, WebSearchResult, RAGResult, Session
from model.user import User
from model.uploads import UploadFile, UploadPic

"""注册用户"""
def user_register(username, password):
    # 检查用户是否已存在
    user = User.query.filter_by(username=username).first()
    if user:
        return False, "注册失败，用户已存在"
    # 注册新用户
    try:
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return True, new_user.id
    except Exception as e:
        db.session.rollback()
        return False, str(e)

"""用户登录"""
def user_login(username):
    user = User.query.filter_by(username=username).first()
    if user:
        return True, user
    return False, "User not found"

"""创建一个新的会话"""
def create_session(session_id):
    try:
        new_session = Session(session_id=session_id)
        db.session.add(new_session)
        db.session.commit()
        return True, session_id
    except Exception as e:
        db.session.rollback()
        return False, str(e)

def add_question_to_session(session_id, content):
    """向会话中添加问题"""
    try:
        session = Session.query.filter_by(session_id=session_id).first()
        if not session:
            return False, "Session not found"
        
        new_question = Question(session_id=session_id, content=content)
        db.session.add(new_question)
        db.session.commit()
        return True, new_question.id
    except Exception as e:
        db.session.rollback()
        return False, str(e)


def add_question_answer(question_id, answer):
    question = Question.query.filter_by(id=question_id).first()
    if not question:
        return False, "Question not found"

    question.answer = answer
    db.session.commit()
    return True, question.id

def add_question_summary(question_id, summary):
    question = Question.query.filter_by(id=question_id).first()
    if not question:
        return False, "Question not found"

    question.summary = summary
    db.session.commit()
    return True, question.id

def get_question_by_id(question_id):
    """根据问题ID获取问题"""
    current_question = Question.query.filter_by(id=question_id).first()
    
    return True, current_question

def get_answer_by_question_id(question_id):
    """根据问题ID获取回答"""
    question = Question.query.filter_by(id=question_id).first()
    if not question:
        return False, "Question not found"

    return True, question.answer

def get_previous_questions(session_id, question_id):
    """获取先前的问题"""
    previous_questions = Question.query.filter(
        Question.session_id == session_id, Question.id < question_id
    ).order_by(Question.id.desc()).limit(5).all()
    return True, previous_questions

def add_web_search_result(question_id, web_search_result):
    """添加网络搜索结果"""
    question = Question.query.filter_by(id=question_id).first()
    if not question:
        return False, "Question_Id not found"

    web_search_result = WebSearchResult(question_id=question_id, content=web_search_result)
    db.session.add(web_search_result)
    db.session.commit()
    return True, web_search_result.id

def add_rag_result(question_id, rag_result):
    """添加RAG结果"""
    question = Question.query.filter_by(id=question_id).first()
    if not question:
        return False, "Question_Id not found"

    rag_result = RAGResult(question_id=question_id, content=rag_result)
    db.session.add(rag_result)
    db.session.commit()

    return True, rag_result.id

def create_apisession(session_id, api_session_id=None):
    """获取或创建API会话"""
    api_session = ApiSession.query.filter_by(session_id=session_id).first()
    if not api_session:
        api_session = ApiSession(session_id=session_id, api_session_id=api_session_id)
        db.session.add(api_session)
        db.session.commit()

    return True, api_session.api_session_id

def get_apisession(session_id):
    """获取API会话"""
    api_session = ApiSession.query.filter_by(session_id=session_id).first()
    if not api_session:
        return False, None

    return True, api_session.api_session_id

# 用户上传文件(docx / pptx / xlsx)
def add_upload_file(user_id, file_name, file_url):
    try:
        new_file = UploadFile(user_id=user_id, file_name=file_name, file_url=file_url)
        db.session.add(new_file)
        db.session.commit()
        return True, "success upload file"
    except Exception as e:
        db.session.rollback()
        # 打印完整的异常信息
        current_app.logger.error(f"Error adding file: {e}")
        current_app.logger.error(traceback.format_exc())
        return False, str(e)

# 用户上传图片(jpg / png / jpeg)
def add_pic_file(user_id, pic_name, pic_url, ocr_msg):
    try:
        new_pic = UploadPic(user_id=user_id, pic_name=pic_name, pic_url=pic_url, ocr_msg=ocr_msg)
        db.session.add(new_pic)
        db.session.commit()
        return True, "success upload pic"
    except Exception as e:
        db.session.rollback()
        # 打印完整的异常信息
        current_app.logger.error(f"Error adding file: {e}")
        current_app.logger.error(traceback.format_exc())
        return False, str(e)