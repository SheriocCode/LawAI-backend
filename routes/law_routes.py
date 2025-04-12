from flask import Blueprint, request
import time
import json
import random
from utils.result import error_response, success_response
from utils.jwt import generate_token, token_required
from db import get_judicial_case_by_id, get_judgment_document_by_id, get_judicial_direction_cases_board, get_judicial_reference_cases_board
from db import get_judgement_count, get_judgement_docs_board
from db import get_hot_cases, get_interest, get_related_judgment
from db import get_docs_recommend
from db import get_collect_dashboard, get_collect_laws, get_collect_cases, get_collect_docs
from db import get_case_knowledge_graph

from algo.search import find_similar_cases

from extension import console
from extension import model, embeddings, metadata

law_bp = Blueprint('law', __name__)

# 首页搜索
@law_bp.route('/search', methods=['POST'])
def search():
    data = request.json
    query_str = data.get('user_input')
    if not query_str:
        return error_response('请输入关键词')
    
    # 案例搜索开始计时
    case_search_start_time = time.time()

    top_k = 20
    results = find_similar_cases(model, embeddings, metadata, query_str, top_k)
    
    # 展示结果
    for rank, (idx, score) in enumerate(results, 1):
        print('原索引:', idx, ' 相似度:', score)
        case_info = metadata[idx]
        print(f"\n▌ 相似度排名 {rank} （相似度：{score:.4f}）")
        print(f"案例标题：{case_info['案例']}")
        print(f"核心关键词：{', '.join(case_info['关键词'])}")
        print(f"裁判要旨：{case_info['基本案情']}")

    # 结束计时
    case_search_end_time = time.time()
    case_search_execution_time = case_search_end_time - case_search_start_time
    
    res = {
        "search_time": round(case_search_execution_time, 2),
        "search_res": {
            "count": len(results), 
            "items": [ 
                {
                    "doc_id": int(item[0])+1,
                    "index": idx,
                    "title": metadata[item[0]]['案例'],
                    "keywords": metadata[item[0]]['关键词'],
                    "judgment_short": metadata[item[0]]['基本案情'],
                    "doc_type": "JUDICIAL_CASES", 
                    "score": float(item[1]),
                } for idx, item in enumerate(results)
            ]
        }
    }
    return success_response(res)


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
def related_judgment():
    # 获取查询参数
    query_params = request.args.to_dict()
    judgment_document_id = query_params.get('judgment_document_id')
    console.print('[green]judgment_document_id:[/green]', judgment_document_id)

    # TODO: 获取相关判决
    success, judgments = get_related_judgment(judgment_document_id)
    if not success:
        return error_response(judgments)

    res = {
        "count": 10,  
        "related_judgment": [
            {
                "doc_id": item.id,
                "title": item.title,
                "doc_type": "JUDGMENT_DOCUMENT",
                "trial_procedure": item.trial_procedure,
                "cause": item.cause.split('、') if item.cause else [],
            } for judgment in judgments for  item in judgment
        ]
    }

    return success_response(res)


# 获取热门案例
@law_bp.route('/hot_cases', methods=['GET'])
def hot_cases():
    # TODO: 热门案例获取

    success, hot_cases = get_hot_cases()
    if not success:
        return error_response(hot_cases)

    res = {
        "count": len(hot_cases), 
        "items": [
            {
                "doc_id": item.id, 
                "index": idx,
                "title": item.title,
                "keywords": item.keywords.split(' '),
            } for idx, item in enumerate(hot_cases)
        ]
    }

    return success_response(res)


# 用户推荐-猜您想看
@law_bp.route('/interest', methods=['GET'])
@token_required
def interest():
    # TODO
    # 基于用户画像进行相关推荐

    # 获取用户的推荐数据
    success, case_interest, document_interest = get_interest()

    case_items = [
        {
            "doc_id": item.id,
            "index": idx,
            "title": item.title,
            "doc_type": "JUDICIAL_CASES"
        } for idx, item in enumerate(case_interest)
    ]

    document_items = [
        {
            "doc_id": item.id,
            "index": idx,
            "title": item.title,
            "doc_type": "JUDGMENT_DOCUMENT"
        } for idx, item in enumerate(document_interest, len(case_interest)) 
    ]

    res = {
        "count": len(case_interest) + len(document_interest), 
        "items": case_items + document_items
    }


    return success_response(res)


# 法律法规页面
@law_bp.route('/legal_rules', methods=['GET'])
def legal_rules_board():
    # 读取laws.json文件
    with open('static/laws.json', 'r', encoding='utf-8') as file:
        laws_data = json.load(file)
    
    # 构建法律法规数据
    legal_rules_board = []
    laws_type = []

    for law in laws_data:
        if law['folder_name'] not in laws_type:
            laws_type.append(law['folder_name'])
            current_folder_name = law['folder_name']
            legal_rules_board.append({
                "board_index": laws_type.index(current_folder_name) + 1,
                "board_title": current_folder_name,
                "laws": [
                    {
                        "doc_id": law['id'],
                        "title": law['law_name'],
                        "doc_type": "LEGAL_RULES"
                    } for law in laws_data if law['folder_name'] == current_folder_name
                ]
            })

    res = {
        "data_board": {
            "storage_count": 512,
            "category_count": 32,
            "visit_count": 1024
        },
        "legal_rules_board": legal_rules_board
    }
    return success_response(res)


# 司法案例页面
@law_bp.route('/judicial_cases', methods=['GET'])
def judicial_cases_board():
    # 加载case_top_keywords
    with open('static/case_top_keywords.json', 'r', encoding='utf-8') as file:
        case_top_keywords = json.load(file)

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
            },
            "keywords_chart_data": case_top_keywords[category["title"]]
        }

    # 生成 judicial_cases_board
    judicial_cases_board = list(map(lambda category, index: create_board(category, index), categories, range(len(categories))))

    # 构建最终结果
    res = {
        "judicial_cases_board": judicial_cases_board,
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
                "xingzheng": ["许可", "处罚", "强制措施", "确认", "裁决", "复议", "诉讼", "合同", "给付", "指导", "征收", "赔偿", "责任", "处分", "主体", "行为", "程序", "规范性文件", "立法", "执法"]
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
    success, recommend_cases, recommend_docs, recommend_laws, recommend_litigations = get_docs_recommend()
    if not success:
        return error_response(recommend_cases)
    
    reasons = [
        "最近浏览相关主题",
        "AI对话中的相关主题",
        "偏好推荐",
        "协同过滤推荐",
        "内容的推荐",
        "基于用户行为的推荐",
        "热门司法文书案例",
        "数据趋势分析结果",
        "相似推荐",
        "历史查询记录推荐",
        "司法领域专家推荐",
        "基于数据挖掘的结果",
        "结合法律条文的推荐"
    ]

    res = {
        "document_recommend": {
            "count": len(recommend_docs),
            "items": [
                {
                    "doc_id": item.id,
                    "index": idx,
                    "title": item.title,
                    "cause": item.cause.split('、') if item.cause else [],
                    "trial_procedure": item.trial_procedure,
                    "judgment_date": item.judgment_date,
                    "doc_type": "JUDGMENT_DOCUMENTS",
                    # 随机选择一个理由
                    "recommend_reason": random.choice(reasons)
                } for idx, item in enumerate(recommend_docs)
            ]
        },
        "law_recommend":{
            "count": len(recommend_laws),
            "items": [
                {
                    "doc_id": item.id,
                    "index": idx,
                    "title": item.title,
                    "law_category": item.law_category,
                    "doc_type": "LAWS",
                    "recommend_reason": random.choice(reasons)
                } for idx, item in enumerate(recommend_laws)
            ]
        },
        "guides_recommend":{
            "count": len(recommend_litigations),
            "items": [
                {
                    "doc_id": item.id,
                    "index": idx,
                    "title": item.title,
                    "publisher": item.publisher,
                    "doc_type": "LITIGATION_GUIDES",
                    "recommend_reason": random.choice(reasons)
                } for idx, item in enumerate(recommend_litigations)
            ]
        }
    }

    return success_response(res)


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
    with open('static/law_category.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    return success_response(data)

# 图标-法院地图
@law_bp.route('/chart/court_map', methods=['GET'])
def court_map():
    # 读取json
    with open('static/court_category.json', 'r', encoding='utf-8') as f:
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

    return success_response(processed_data)

# 法律知识图谱-案例知识图谱
@law_bp.route('/graph/case_knowledge_graph', methods=['GET'])
def case_knowledge_graph():
    keyword = request.args.get('keyword', '').lower()
    if not keyword:
        return error_response('请输入关键词')
    
    success, graph_data = get_case_knowledge_graph(keyword)
    if not success:
        return error_response(graph_data)


    # 将查询结果转换为 JSON 格式
    matched_data = []
    for result in graph_data:
        matched_data.append({
            '案例': result.title,
            '关键词': result.keywords.split(' ') if result.keywords else [],
            '关联索引': [result.related_laws.split('&&') if result.related_laws else []]
        })

    # return jsonify(matched_data)
    return success_response(matched_data)
