from flask import Blueprint, request
from utils.result import error_response, success_response
from utils.jwt import generate_token, token_required
from db import get_judicial_case_by_id, get_judgment_document_by_id, get_legal_rules_board, get_judicial_direction_cases_board, get_judicial_reference_cases_board

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

