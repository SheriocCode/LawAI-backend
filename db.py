# db.py
from flask import current_app
import traceback
from extension import db
from model.ai import ApiSession, Question, WebSearchResult, RAGResult, Session
from model.user import User, Collect, UserSession
from model.law import JudicalCase, JudgmentDocument, Law, LitigationDocument
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

# 用户与session关联
def associate_user_with_session(user_id, session_id):
    # 用户与session关联表
    try:
        new_association = UserSession(user_id=user_id, session_id=session_id)
        db.session.add(new_association)
        db.session.commit()
        return True, "Association created successfully"
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

def get_retrieve_data(question_id):
    """获取检索数据"""
    web_search_result = WebSearchResult.query.filter_by(question_id=question_id).first()
    rag_result = RAGResult.query.filter_by(question_id=question_id).first()

    res = {
        "web_search_result": web_search_result,
        "rag_result": rag_result
    }
    
    return True, res


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

# 添加session title
def add_session_title(session_id, title):
    session = Session.query.filter_by(session_id=session_id).first()
    if not session:
        return False, "Session not found"

    session.title = title
    db.session.commit()
    return True, session.id

# 获取用户历史AI会话
def get_user_history_sessions(user_id):
    # 获取用户的所有session_id
    user_sessions = UserSession.query.filter_by(user_id=user_id).all()
    # 查找每个session_id对应的session
    sessions = []
    for user_session in user_sessions:
        session = Session.query.filter_by(session_id=user_session.session_id).first()
        if session:
            sessions.append(session)
    return True, sessions

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

# 案例具体页-获取热门案例
def get_hot_cases():
    # 获取judical_case表中id从301-310的案例
    hot_cases = JudicalCase.query.filter(JudicalCase.id >= 301, JudicalCase.id <= 310).all()
    return True, hot_cases

# 用户推荐-猜您想看
def get_interest():
    # 随机获取judical_case表中5个案例
    case_interest = JudicalCase.query.order_by(db.func.random()).limit(5).all()
    # 随机获取judgment_document表中5个案例
    document_interest = JudgmentDocument.query.order_by(db.func.random()).limit(5).all()

    return True, case_interest, document_interest

# 根据id获取裁判文书具体信息
def get_judgment_document_by_id(id):
    judgment_document = JudgmentDocument.query.get(id)
    if judgment_document:
        return True, judgment_document
    else:
        return False, "Judgment document not found"
    
# 获取id裁判文书的相关判决
def get_related_judgment(id):
    # TODO：相关判决获取方式

    # 获取民事判决5条,从id为115开始
    civil_judgment = JudgmentDocument.query.filter(JudgmentDocument.document_type == '民事案件', JudgmentDocument.id >= 115).limit(5).all()
    # 获取刑事判决5条
    criminal_judgment = JudgmentDocument.query.filter(JudgmentDocument.document_type == '刑事案件', JudgmentDocument.id!= id).limit(5).all()

    judgments = [civil_judgment, criminal_judgment]

    return True, judgments


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
def get_judgement_count(doc_type=None):
    if doc_type == '刑事':
        count = JudgmentDocument.query.filter(JudgmentDocument.document_type.like('%刑事%')).count()
    elif doc_type == '民事':
        count = JudgmentDocument.query.filter(JudgmentDocument.document_type.like('%民事%')).count()
    elif doc_type == '行政':
        count = JudgmentDocument.query.filter(JudgmentDocument.trial_procedure.like('%行政%')).count()
    else:
        count = JudgmentDocument.query.count()
    return count

# 裁判文书页面
def get_judgement_docs_board():
    # 获取关键词中包含 “刑事” 的判决书 前15个
    criminal_judgement_docs = JudgmentDocument.query.filter(JudgmentDocument.document_type.like('%刑事%')).limit(15).all()
    # 获取关键词中包含 “民事” 的判决书
    civil_judgement_docs = JudgmentDocument.query.filter(JudgmentDocument.document_type.like('%民事%')).limit(15).all()
    # 获取关键词中包含 “行政” 的判决书
    # TODO:行政判决书数据量不足，格式不统一
    administrative_judgement_docs = JudgmentDocument.query.filter(JudgmentDocument.trial_procedure.like('%行政%')).limit(10).all()
    # TODO: 获取其他类型判决书

    return True, criminal_judgement_docs, civil_judgement_docs, administrative_judgement_docs

# 案例文书推荐
def get_docs_recommend():
    # TODO： 基于用户行为获取案例文书推荐
    # 随机获取案例15个
    case_judgement_docs = JudicalCase.query.order_by(db.func.random()).limit(15).all()
    # 随机获取裁判文书15个
    document_judgement_docs = JudgmentDocument.query.order_by(db.func.random()).limit(15).all()
    # 随机获取法律文书15个
    law_judgement_docs = Law.query.order_by(db.func.random()).limit(15).all()
    # 获取诉讼文书15个
    litigation_judgement_docs = LitigationDocument.query.order_by(db.func.random()).limit(15).all()

    return True, case_judgement_docs, document_judgement_docs, law_judgement_docs, litigation_judgement_docs
    
    
    
# 法律知识图谱-案例知识图谱
def get_case_knowledge_graph(keyword):
    # 查询匹配的案例
    results = JudicalCase.query.filter(
        (JudicalCase.title.ilike(f'%{keyword}%')) |
        (JudicalCase.keywords.ilike(f'%{keyword}%')) |
        (JudicalCase.related_laws.ilike(f'%{keyword}%'))
    ).limit(20).all()

    return True, results


# 获取用户收藏统计
def get_collect_dashboard(user_id):
    # 获取用户收藏法律文书统计
    collect_laws_count = Collect.query.filter_by(user_id=user_id, doc_type='LAWS').count()

    # 获取用户收藏案例统计
    collect_case_count = Collect.query.filter_by(user_id=user_id, doc_type='JUDICIAL_CASES').count()
    
    # 获取用户收藏的判决书统计
    collect_doc_count = Collect.query.filter_by(user_id=user_id, doc_type='JUDGMENT_DOCS').count()

    # 案例文书统计
    sum_case_doc_count = collect_case_count + collect_doc_count

    return True, collect_laws_count, sum_case_doc_count

# 获取用户收藏-法律文书收藏
def get_collect_laws(user_id):
    collect_laws_count = Collect.query.filter_by(user_id=user_id, doc_type='LAWS').count()
    collect_laws = Collect.query.filter_by(user_id=user_id, doc_type='LAWS').limit(10).all()

    collect_list = []
    # 获取对应的法律文书
    for idx, collect_law in enumerate(collect_laws):
        law = Law.query.get(collect_law.doc_id)
        collect_list.append({
            "doc_id": law.id,
            "index": idx,
            "title": law.title,
            "law_category": law.law_category,
            "doc_type": "LAWS",
            "collect_date": collect_law.collect_date.strftime("%Y-%m-%d")
        })

    return True, collect_list, collect_laws_count

# 获取用户收藏-案例
def get_collect_cases(user_id):
    collect_cases_count = Collect.query.filter_by(user_id=user_id, doc_type='JUDICIAL_CASES').count()
    collect_cases = Collect.query.filter_by(user_id=user_id, doc_type='JUDICIAL_CASES').limit(10).all()

    collect_list = []
    # 获取对应的案例
    for idx, collect_case in enumerate(collect_cases):
        case = JudicalCase.query.get(collect_case.doc_id)
        collect_list.append({
            "doc_id": case.id,
            "index": idx,
            "title": case.title,
            "keywords": case.keywords.split(' '),
            "doc_type": "JUDICIAL_CASES",
            "collect_date": collect_case.collect_date.strftime("%Y-%m-%d")
        })

    return True, collect_list, collect_cases_count

# 获取用户收藏-裁判文书
def get_collect_docs(user_id):
    collect_docs_count = Collect.query.filter_by(user_id=user_id, doc_type='JUDGMENT_DOCUMENTS').count()
    collect_docs = Collect.query.filter_by(user_id=user_id, doc_type='JUDGMENT_DOCUMENTS').limit(10).all()

    collect_list = []
    # 获取对应的法律文书
    for idx, collect_doc in enumerate(collect_docs):
        doc = JudgmentDocument.query.get(collect_doc.doc_id)
        collect_list.append({
            "doc_id": doc.id,
            "index": idx,
            "title": doc.title,
            "cause": doc.cause.split('、') if doc.cause else [],
            "doc_type": "JUDGMENT_DOCUMENTS",
            "collect_date": collect_doc.collect_date.strftime("%Y-%m-%d")
        })

    return True, collect_list, collect_docs_count