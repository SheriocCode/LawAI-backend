# db.py
from flask import current_app
import traceback
from extension import db
from model.ai import ApiSession, Question, WebSearchResult, RAGResult, Session
from model.user import User
from model.law import JudicalCase, JudgmentDocument
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

# 获取用户信息
def get_user_by_id(user_id):
    user = User.query.filter_by(id=user_id).first()
    return True, user

# 修改用户信息
def update_user_info(user_id, username, avatar, password, signature, gender):
    user = User.query.filter_by(id=user_id).first()
    # 更新用户信息
    if username is not None:
        user.username = username
    if avatar is not None:
        user.avatar = avatar
    if password is not None:
        user.password = password  # 注意：实际应用中密码应加密存储
    if signature is not None:
        user.signature = signature
    if gender is not None:
        user.gender = gender
    try:
        db.session.commit()
        return True, user
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

# 根据id获取法院案例具体信息
def get_judicial_case_by_id(id):
    judicial_case = JudicalCase.query.get(id)
    if judicial_case:
        return True, judicial_case
    else:
        return False, "Judicial case not found"

# 根据id获取裁判文书具体信息
def get_judgment_document_by_id(id):
    judgment_document = JudgmentDocument.query.get(id)
    if judgment_document:
        return True, judgment_document
    else:
        return False, "Judgment document not found"
    
# 法律法规页面
def get_legal_rules_board():
    pass


# 司法案例页面-获取指导性案例
def get_judicial_direction_cases_board():
    # 获取关键词中包含 “刑事” 且 title中包含 “指导” 的案例 前10个
    criminal_direction_cases = JudicalCase.query.filter(JudicalCase.keywords.like('%刑事%'), JudicalCase.title.like('%指导%')).limit(10).all()
    # 获取关键词中包含 “民事” 且 title中包含 “指导” 的案例
    civil_direction_cases = JudicalCase.query.filter(JudicalCase.keywords.like('%民事%'), JudicalCase.title.like('%指导%')).limit(10).all()
    # 获取关键词中包含 “行政” 且 title中包含 “指导” 的案例
    administrative_direction_cases = JudicalCase.query.filter(JudicalCase.keywords.like('%行政%'), JudicalCase.title.like('%指导%')).limit(10).all()
    # 获取关键词中包含 “赔偿” 且 title中包含 “指导” 的案例
    compensation_direction_cases = JudicalCase.query.filter(JudicalCase.keywords.like('%赔偿%'), JudicalCase.title.like('%指导%')).limit(10).all()
    # 获取关键词中包含 “执行” 且 title中包含 “指导” 的案例
    execution_direction_cases = JudicalCase.query.filter(JudicalCase.keywords.like('%执行%'), JudicalCase.title.like('%指导%')).limit(10).all()

    return True, criminal_direction_cases, civil_direction_cases, administrative_direction_cases, compensation_direction_cases, execution_direction_cases

# 司法案例页面-获取参考性案例
def get_judicial_reference_cases_board():
    # 获取关键词中包含 “刑事” 且 title中不包含 “指导” 的案例 前10个
    criminal_reference_cases = JudicalCase.query.filter(JudicalCase.keywords.like('%刑事%'), JudicalCase.title.notlike('%指导%')).limit(10).all()
    # 获取关键词中包含 “民事” 且 title中不包含 “指导” 的案例
    civil_reference_cases = JudicalCase.query.filter(JudicalCase.keywords.like('%民事%'), JudicalCase.title.notlike('%指导%')).limit(10).all()
    # 获取关键词中包含 “行政” 且 title中不包含 “指导” 的案例
    administrative_reference_cases = JudicalCase.query.filter(JudicalCase.keywords.like('%行政%'), JudicalCase.title.notlike('%指导%')).limit(10).all()
    # 获取关键词中包含 “赔偿” 且 title中不包含 “指导” 的案例
    compensation_reference_cases = JudicalCase.query.filter(JudicalCase.keywords.like('%赔偿%'), JudicalCase.title.notlike('%指导%')).limit(10).all()
    # 获取关键词中包含 “执行” 且 title中不包含 “指导” 的案例
    execution_reference_cases = JudicalCase.query.filter(JudicalCase.keywords.like('%执行%'), JudicalCase.title.notlike('%指导%')).limit(10).all()

    return True, criminal_reference_cases, civil_reference_cases, administrative_reference_cases, compensation_reference_cases, execution_reference_cases


# 裁判文书页面-获取count
def get_judgement_count():
    count = JudgmentDocument.query.count()
    return True, count

# 裁判文书页面
def get_judgement_docs_board():
    # 获取关键词中包含 “刑事” 的判决书 前15个
    criminal_judgement_docs = JudgmentDocument.query.filter(JudgmentDocument.document_type.like('%刑事%')).limit(15).all()
    # 获取关键词中包含 “民事” 的判决书
    civil_judgement_docs = JudgmentDocument.query.filter(JudgmentDocument.document_type.like('%民事%')).limit(15).all()
    # 获取关键词中包含 “行政” 的判决书
    administrative_judgement_docs = JudgmentDocument.query.filter(JudgmentDocument.document_type.like('%行政%')).limit(15).all()
    # TODO: 获取其他类型判决书

    return True, criminal_judgement_docs, civil_judgement_docs, administrative_judgement_docs

# 案例文书推荐
def get_docs_recommend():
    # TODO： 基于用户行为获取案例文书推荐
    pass