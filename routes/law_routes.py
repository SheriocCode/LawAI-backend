from flask import Blueprint, request
import json
from utils.result import error_response, success_response
from utils.jwt import generate_token, token_required
from db import get_judicial_case_by_id, get_judgment_document_by_id, get_legal_rules_board, get_judicial_direction_cases_board, get_judicial_reference_cases_board
from db import get_judgement_count, get_judgement_docs_board
from db import get_docs_recommend
from db import get_collect_dashboard, get_collect_laws, get_collect_cases, get_collect_docs

from extension import console

law_bp = Blueprint('law', __name__)

# 获取id案例具体信息
@law_bp.route('/page/judicial_case/<int:id>', methods=['GET'])
def get_judicial_case(id):
    success, msg = get_judicial_case_by_id(id)
    if not success:
        return error_response(msg)

    # TODO: 查找聚类中和该案例相关的related_category
    related_category = [{"category": "合同纠纷", "score": 40}, {"category": "侵权责任", "score": 79}]
    
    res = {
        "case_title": msg.title,
        "keywords": msg.keywords.split(' '),
        "related_laws": msg.related_laws.split('&&'),
        "related_trial": msg.related_trial,
        "content": {
            "basic_facts": msg.basic_facts,
            "judgment_reasons": msg.judgment_reasons,
            "judgment_essence": msg.judgment_essence
        },
        "related_category": related_category
    }

    return success_response(res)


# 获取id裁判文书具体信息
@law_bp.route('/page/judgment_document/<int:id>', methods=['GET'])
def get_judgment_document(id):
    success, msg = get_judgment_document_by_id(id)
    if not success:
        return error_response(msg) 
    
    # TODO: 查找聚类中和该文书相关的related_keywords
    related_keywords = [{"keyword": "盗窃", "score": 40}, {"keyword": "诈骗", "score": 79}]
    
    # 反序列化法律依据
    def deserialize_law_basis(serialized_law_basis):
        if not serialized_law_basis:
            return []

        # 按 '&&' 分割，得到每个法律依据的组合
        law_basis_items = serialized_law_basis.split('&&')

        law_basis_list = []

        for item in law_basis_items:
            if '@' in item:
                # 按 '@' 分割，提取法律名称和条款
                law_name, articles = item.split('@', 1)
                # 将条款字符串按空格分割，还原为条款列表
                articles_list = articles.split()
                # 构建法律依据字典
                law_basis_list.append({
                    'law_name': law_name,
                    'articles': articles_list
                })

        return law_basis_list

    res = {
        "title": msg.title,
        "basic_infomation": {
            "trial_court": msg.trial_court,
            "trial_procedure": msg.trial_procedure,
            "type": msg.document_type,
            "judgment_date": msg.judgment_date,
            "cause": msg.cause.split('、') if msg.cause else [],
            "client": msg.client.split('、') if msg.client else []
        },
        "law_basis": deserialize_law_basis(msg.law_basis),
        "content": {
            "title": msg.title,
            "category": msg.category,
            "decision_num": msg.decision_num,
            "details": msg.details
        },
        "related_keywords": related_keywords
    }

    return success_response(res)


# 获取id裁判文书相关判决
@law_bp.route('/related_judgment', methods=['GET'])
def get_related_judgment():
    # 获取查询参数
    query_params = request.args.to_dict()
    judgment_documnet_id = query_params.get('judgment_documnet_id')
    console.print('[green]judgment_documnet_id:[/green]', judgment_documnet_id)

    # TODO: 获取相关判决

    return success_response('success')


# 获取用户个性化推荐
@law_bp.route('/interest', methods=['GET'])
@token_required
def interest():
    # TODO
    # 基于用户画像进行相关推荐

    # 获取用户的推荐数据

    return success_response('success')


# 法律法规页面
@law_bp.route('/legal_rules', methods=['GET'])
def legal_rules_board():
    # TODO: 从数据库中获取法律法规数据
    pass


# 司法案例页面
@law_bp.route('/judicial_cases', methods=['GET'])
def judicial_cases_board():
    # 获取指导性案例
    success, criminal_direction_cases, civil_direction_cases, administrative_direction_cases, compensation_direction_cases, execution_direction_cases = get_judicial_direction_cases_board()
    # 获取参考性案例
    success, criminal_reference_cases, civil_reference_cases, administrative_reference_cases, compensation_reference_cases, execution_reference_cases = get_judicial_reference_cases_board()

   # 定义map数据
    categories = [
        {"title": "刑事", "direction_cases": criminal_direction_cases, "reference_cases": criminal_reference_cases},
        {"title": "民事", "direction_cases": civil_direction_cases, "reference_cases": civil_reference_cases},
        {"title": "行政", "direction_cases": administrative_direction_cases, "reference_cases": administrative_reference_cases},
        {"title": "国家赔偿", "direction_cases": compensation_direction_cases, "reference_cases": compensation_reference_cases},
        {"title": "执行", "direction_cases": execution_direction_cases, "reference_cases": execution_reference_cases}

    ]

    # 使用 map 函数动态生成 judicial_cases_board
    def create_board(category, index):
        return {
            "board_index": index + 1,
            "board_title": category["title"],
            "guidance_cases_board": {
                "count": len(category["direction_cases"]),
                "items": [
                    {
                        "doc_id": case.id,
                        "index": idx,
                        "title": case.title,
                        "doc_type": "JUDICIAL_CASES"
                    } for idx, case in enumerate(category["direction_cases"])
                ]
            },
            "reference_cases_board": {
                "count": len(category["reference_cases"]),
                "items": [
                    {
                        "doc_id": case.id,
                        "index": idx,
                        "title": case.title,
                        "doc_type": "JUDICIAL_CASES"
                    } for idx, case in enumerate(category["reference_cases"])
                ]
            }
        }

    # 生成 judicial_cases_board
    judicial_cases_board = list(map(lambda category, index: create_board(category, index), categories, range(len(categories))))

    # 构建最终结果
    res = {
        "judicial_cases_board": judicial_cases_board
    }
        
    return success_response(res)


# 裁判文书页面
@law_bp.route('/judgement_docs', methods=['GET'])
def judgement_docs_board():
    # 获取裁判文书总数量
    success, judgement_count = get_judgement_count()
    # 获取裁判文书数据
    success, criminal_judgement_docs, civil_judgement_docs, administrative_judgement_docs = get_judgement_docs_board()

    # 定义map数据
    categories = [
        {"title": "刑事", "judgement_docs": criminal_judgement_docs},
        {"title": "民事", "judgement_docs": civil_judgement_docs},
        {"title": "行政", "judgement_docs": administrative_judgement_docs}
    ]

    # 使用 map 函数动态生成 judgement_docs_board
    def create_board(category, index):
        return {
            "index": index + 1, 
            "title": category["title"],
            "count": len(category["judgement_docs"]),
            "items": [
                {
                    "index": idx,
                    "doc_id": doc.id,
                    "title": doc.title,
                    "cause": doc.cause.split('、') if doc.cause else [],
                    "trial_procedure": doc.trial_procedure,
                    "judgment_date": doc.judgment_date,
                    "doc_type": "JUDGMENT_DOCS"
                } for idx, doc in enumerate(category["judgement_docs"])
            ]
        }

    # 生成 judgement_docs_board
    judgement_docs_board = list(map(lambda category, index: create_board(category, index), categories, range(len(categories))))

    # 构建最终结果
    res = {
        "data_board": {
            "judgement_count": judgement_count,
            "word_panel": {
                "xingshi": ['非法占有', '自首', '罚金', '减轻处罚', '交通事故', '从犯', '共同犯罪', '拘役', '故意犯', '管制', '交通肇事', '违法所得', '没收', '附带民事诉讼', '偶犯', '犯罪未遂', '主要责任', '财产权', '鉴定', '误工费', '人身权利', '人身损害赔偿', '扣押', '传唤', '立功', '返还', '程序合法', '合法财产', '伪造', '聚众', '所有权', '赔偿责任', '共同故意', '胁迫', '过失'],
                "minshi": ['合同', '利息', '利率', '合同约定', '违约金', '民间借贷', '强制性规定', '贷款', '返还', '驳回', '清偿', '借款合同', '交通事故', '担保', '违约责任', '鉴 定', '给付', '交付', '人身损害赔偿', '误工费', '保证', '传票', '买卖合同', '债权', '传唤'],
                # TODO: 行政关键词
                "xingzheng": [
                "XXX"
                ]
            }
        },
        "judgement_docs_board": judgement_docs_board
    }

    return success_response(res)


# 获取案例文书推荐
@law_bp.route('/docs_recommend', methods=['GET'])
@token_required
def docs_recommend():
    # TODO： 基于用户行为获取案例文书推荐
    get_docs_recommend()
    pass


# 获取用户收藏统计
@law_bp.route('/collect/dashboard', methods=['GET'])
@token_required
def collect_dashboard():
    user_id = request.user_id
    success, collect_laws_count, sum_case_doc_count = get_collect_dashboard(user_id)
    
    res = {
        'law_collect': collect_laws_count,
        'case_doc_collect': sum_case_doc_count
    }
    return success_response(res)

# 获取用户收藏-法律文书收藏
@law_bp.route('/collect/law_collect', methods=['GET'])
@token_required
def collect_law_collect():
    user_id = request.user_id
    success, collect_list, collect_laws_count = get_collect_laws(user_id)
    res = {
        'count': collect_laws_count,
        'collect_list': collect_list
    }
    return success_response(res)


# 获取用户收藏-案例收藏
@law_bp.route('/collect/case_collect', methods=['GET'])
@token_required
def collect_case_collect():
    user_id = request.user_id
    success, collect_list, collect_cases_count = get_collect_cases(user_id)
    res = {
        'count': collect_cases_count,
        'collect_list': collect_list
    }
    return success_response(res)

# 获取用户收藏-文书收藏
@law_bp.route('/collect/doc_collect', methods=['GET'])
@token_required
def collect_doc_collect():
    user_id = request.user_id
    success, collect_list, collect_docs_count = get_collect_docs(user_id)
    res = {
        'count': collect_docs_count,
        'collect_list': collect_list
    }
    return success_response(res)

# 图表-法典关系图
@law_bp.route('/chart/law_relation', methods=['GET'])
def law_relation():
    # 读取json
    with open('E:\Desktop\LawAI\LawAI-dataend\data\law_category.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    return success_response(data)

# 图标-法院地图
@law_bp.route('/chart/court_map', methods=['GET'])
def court_map():
    # 读取json
    with open('E:\Desktop\LawAI\LawAI-dataend\data\court_category.json', 'r', encoding='utf-8') as f:
        court_data = json.load(f)

    # provices_list = ['北京市', '天津市', '河北省', '山西省', '内蒙古自治区', '辽宁省', '吉林省', '黑龙江省', '上海市', '江苏省', '浙江省', '安徽省', '福建省', '江西省', '山东省', '河南省', '湖北省', '湖南省', '广东省', '广西壮族自治区', '海南省', '重庆市', '四川省', '贵州省', '云南省', '西藏自治区', '陕西省', '甘肃省', '青海省', '宁夏回族自治区', '新疆维吾尔自治区']
    processed_data = []

    # 处理数据
    result = {}
    for court_json in court_data:
        for key, value in court_json.items():
            court_province = key.split('高级人民法院')[0]
            higher_court = key
            medium_court_list = []
            for medium_court in value:
                for key, value in medium_court.items():
                    medium_court_name = key
                    medium_court_list.append(medium_court_name)
            processed_data.append({
                "court_province": court_province,
                "higher_court": higher_court,
                "medium_court_list": medium_court_list
            })