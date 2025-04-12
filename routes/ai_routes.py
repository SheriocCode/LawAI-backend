from flask import Blueprint, Response, request, current_app, stream_with_context
import uuid
import json
import re
from http import HTTPStatus
import requests

from dashscope import Application

from extension import console, qwen_client, zhipu_client
from config import  AppConfig, ApiKeyConfig, OssConfig, PromptConfig

from utils.result import error_response, success_response
from utils.jwt import generate_token, token_required
from utils.upload import file_uploader

from db import add_pic_file, add_question_answer, add_question_summary, add_upload_file, create_apisession, create_session, add_question_to_session, get_apisession, get_question_by_id, get_answer_by_question_id
from db import add_web_search_result, get_retrieve_data

ai_bp = Blueprint('ai', __name__)

# 提取用户问题关键词
def extract_search_keywords(user_question):
    prompt = PromptConfig.KEYWORD_EXTRACTION_PROMPT + f'用户问题：{user_question}'

    response = qwen_client.chat.completions.create(
        model="qwen-plus",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    
    console.print(f"[yellow](func: extract_search_keywords)[yellow] [green]response:{response}[/green] ")

    try:
        result = json.loads(response.choices[0].message.content)
        if result["related"]:
            return result["keywords"]
        else:
            return []
    except Exception as e:
        console.print(f"[red]Error parsing response: {e}[/red]")
        return []

# 后台进程：对话总结
def background_summary(question_id, full_response):
    response = qwen_client.chat.completions.create(
        model="qwen-plus", 
        messages=[
            {'role': 'system', 'content': 'summarize the following text into a concise summary, without repeating the text'},
            {'role': 'user', 'content': full_response}],
    )
        
    summary = response.choices[0].message.content if response.choices else "No response"
    console.print(f'[purple](back func: background_summary)[/purple] [italic green]summary_result: {summary}[/italic green]')

    try:
        # with app.app_context():
        #     add_question_summary(question_id, summary)
        add_question_summary(question_id, summary)
        console.print(f"[purple](back func: background_summary)Summary saved successfully[/purple]")
    except Exception as e:
        console.print(f"[red]Error submitting background task: {e}[/red]")

# 创建新AI对话
@ai_bp.route("/ai/newchat", methods=["GET"])
@token_required
def new_chat():
    session_id = uuid.uuid4().hex
    success, msg = create_session(session_id)
    if not success:
        return error_response(msg)
    return success_response({"session_id": msg})

@ai_bp.route("/ai/new_question_id", methods=["POST"])
def new_question_id():
    data = request.json
    session_id = data.get("session_id")
    if not session_id:
        return error_response("Session ID not found")

    content = {
        "user_question": data.get("user_question"),
        "ocr_msg": data.get("ocr_msg")
    }

    success, msg = add_question_to_session(session_id, json.dumps(content))
    if not success:
        return error_response(msg)

    return success_response({"question_id": msg})


# 用户上传文件(docx / pptx / xlsx)
@ai_bp.route("/upload/file", methods=["POST"])
@token_required
def upload_file():
    # 获取用户信息
    user_id = request.user_id
    # 获取文件
    file = request.files.get('doc_file')
    if not file:
        return error_response("No file uploaded")
    
    # 上传文件
    res = file_uploader(file)

    # 数据库记录操作
    success, msg = add_upload_file(user_id, res["file_name"], res["file_url"])
    if not success:
        return error_response(msg)

    return success_response({
        "file_url": res["file_url"],
    })

# 用户上传图片(jpg / png / jpeg)
@ai_bp.route("/upload/pic", methods=["POST"])
@token_required
def upload_pic():
    user_id = request.user_id
    # 获取文件
    file = request.files.get('pic')
    if not file:
        return error_response("No file uploaded")
    
    # 上传文件
    res = file_uploader(file)

    # 图片OCR识别
    response = qwen_client.chat.completions.create(
        model="qwen-vl-ocr", 
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": res["file_url"],
                        "min_pixels": 28 * 28 * 4,
                        "max_pixels": 1280 * 784
                    },
                    # 目前为保证识别效果，模型内部会统一使用"Read all the text in the image."作为text的值，用户输入的文本不会生效。
                    {"type": "text", "text": "Read all the text in the image."},
                ]
            }
    ])
    ocr_msg = response.choices[0].message.content
    console.print(f'[green]ocr_result: {ocr_msg[:50]}[/green]')

    # 数据库操作
    success, msg = add_pic_file(user_id, res["file_name"], res["file_url"], ocr_msg)
    if not success:
        return error_response(msg)

    return success_response({
        "img_url": res["file_url"],
        "ocr_msg": ocr_msg
    })



@ai_bp.route("/ai/web_search", methods=["POST"])
def web_search():
    data = request.json
    session_id = data.get("session_id")
    if not session_id:
        return error_response("Session ID not found")
    
    question_id = data.get("question_id")
    success, msg = get_question_by_id(question_id)

    if not success:
        return error_response(msg)
    
    user_question = json.loads(msg.content)["user_question"]

    # 用户问题关键词提取
    console.print(f'[blue]@web_search - extract keywords[/blue]')
    keywords = extract_search_keywords(user_question)
    if not keywords:
        return error_response("No need to search")
    

    # 调用zhipu API 进行搜索
    console.print(f'[blue]@web_search - start search[/blue]')
    resp = requests.post(
        ApiKeyConfig.ZHIPU_BASE_URL,
        json = {
            "request_id": str(uuid.uuid4()),
            "tool": "web-search-pro",
            "stream": False,
            "messages": [
                {
                    "role": "user",
                    "content": ' '.join(keywords)
                }
            ]
        },
        headers={'Authorization': ApiKeyConfig.ZHIPU_API_KEY},
        timeout=300
    )

    print(resp)
    print(resp.content.decode())

    search_res = json.loads(resp.content.decode())["choices"][0]["message"]["tool_calls"][1]["search_result"]

    web_search_items = []
    for item in search_res:
        title = item.get("title", "网络搜索结果")
        content = item.get("content", "")
        link = item.get("link", "")
        icon = item.get("icon", "https://cmarket-1326491424.cos.ap-shanghai.myqcloud.com/04fda82c8fd344a19ffc42cbfc2c61aa.png")
        media = item.get("media", "")
        
        # 使用正则表达式提取发布时间
        match = re.search(r"\d{4}-\d{2}-\d{2}", title)
        if match:
            refer = match.group()  # 提取匹配到的发布时间
        else:
            refer = ""  # 如果没有匹配到发布时间，使用默认值

        web_search_items.append({
            "title": title, 
            "content": content,
            "link": link,
            "icon": icon,
            "media": media,
            "refer": refer
        })


    # 搜索结果入库
    console.print(f'[blue]@web_search - save to db [/blue]')
    # TODO: 整理搜索结果，保留关键信息
    add_web_search_result(question_id, str(search_res))

    return success_response({"type": "web_search_result", "web_search_items": web_search_items})

@ai_bp.route("/ai/rag_search", methods=["POST"])
def rag_search():
    data = request.json
    session_id = data.get("session_id")
    if not session_id:
        return error_response("Session ID not found")

    question_id = data.get("question_id")
    success, msg = get_question_by_id(question_id)

    # rag 搜索
    # TODO: rag 搜索，基于rag-agent

    # TODO: 搜索结果入库
    pass


@ai_bp.route("/ai/stream_chat", methods=["POST"])
def stream_chat():
    data = request.json
    session_id = data.get("session_id")
    if not session_id:
        return error_response("Session ID not found")

    question_id = data.get("question_id")
    success, msg = get_question_by_id(question_id)
    if not success:
        return error_response(msg)

    user_input = json.loads(msg.content)

    # 获取retrieve 数据
    console.print(f'[blue]@stream_chat - get retrieve data[/blue]')
    success, retrieve_data = get_retrieve_data(question_id)
    if success:
        if retrieve_data['web_search_result']:
            console.print(f"[green]retrieve data:[/green]")
            console.print(f"[green]web_search_result: {retrieve_data['web_search_result'].content[:25]}...[/green]")
        if retrieve_data['rag_result']:
            console.print(f"[green]retrieve data:[/green]")
            console.print(f"[green]rag_result: {retrieve_data['rag_result'].content[:25]}...[/green]")
    else:
        console.print(f"[red]Failed to retrieve data for question_id: {question_id}[/red]")

    # 构建消息列表
    messages = []

    messages.append({
        "role": "system",
        "content": """
        你是智法通鉴，一个智能法律助手。
        """
    })

    if not retrieve_data['web_search_result']:
        messages.append({
            "role": "user",
            "content": """
            请从一个法律专业者的角度详细地回答用户,问题对用户的问题给出法律上的详细指导
            1. 用户问题：{user_question}
            2. 图片ocr 识别结果：{ocr_msg}
            """.format(user_question=user_input.get("user_question"), ocr_msg=user_input.get("ocr_msg"))
        })
    else:
        messages.append({
            "role": "user",
            "content": """
            参考联网搜索结果，请从一个法律专业者的角度详细地回答用户问题（涉及到案例的请结合搜索结果先介绍案例，不涉及搜索结果的请对用户的问题给出法律上的详细指导）。
            联网搜索结果：{web_search_result}
            1. 用户问题：{user_question}
            2. 图片ocr 识别结果：{ocr_msg}
            """.format(user_question=user_input.get("user_question"), ocr_msg=user_input.get("ocr_msg"), web_search_result=retrieve_data['web_search_result'].content)
        })


    console.print(f'[blue]@stream_chat - start stream chat[/blue]')

    # 获取api_session_id
    success, api_session_id = get_apisession(session_id)
    if not api_session_id:
        # 第一次对话
        responses = Application.call(
                api_key=ApiKeyConfig.DASHSCOPE_API_KEY, 
                app_id=ApiKeyConfig.LONG_SESSION_AGENT_ID,
                # prompt='{user_question} {ocr_msg}'.format(user_question=user_input.get("user_question"), ocr_msg=user_input.get("ocr_msg")),
                messages = messages,
                stream=True,  # 流式输出
                incremental_output=True)  # 增量输出
    else:
        responses = Application.call(
                api_key=ApiKeyConfig.DASHSCOPE_API_KEY, 
                app_id=ApiKeyConfig.LONG_SESSION_AGENT_ID,
                # prompt='{user_question} {ocr_msg}'.format(user_question=user_input.get("user_question"), ocr_msg=user_input.get("ocr_msg")),
                messages = messages,
                session_id = api_session_id,
                stream=True,  # 流式输出
                incremental_output=True)  # 增量输出

    def generate():
        full_response = ""
        for response in responses:
            if response.status_code != HTTPStatus.OK:
                break
            else:
                content = response.output.text
                full_response += content
                print(content, end='')
                yield content

        # TODO: 结果入库
        console.print(f'\n[blue]@stream_chat - save to db(add_question_answer)[/blue]')
        add_question_answer(question_id, full_response)
        api_session_id = response.output.session_id
        create_apisession(session_id, api_session_id)

    return Response(stream_with_context(generate()), content_type="text/plain")

@ai_bp.route("/ai/recommend", methods=["POST"])
def recommend():
    data = request.json
    session_id = data.get("session_id")
    if not session_id:
        return error_response("Session ID not found")

    question_id = data.get("question_id")
    success, msg = get_question_by_id(question_id)
    if not success:
        return error_response(msg)

    success, text = get_answer_by_question_id(question_id)


    console.print(f'[blue]@recommend - start recommend[/blue] base_text: {text[:20]}...')


    response = qwen_client.chat.completions.create(
        model="qwen-max",
        messages=[
            {
            "role": "system",
            "content": '根据文本推荐3个与法律相关的问题，每个问题不超过15个字，问题前添加表情或相关符号，只返回JSON数组。示例：["🤔合同法保障的是什么？","📃劳务合同纠纷如何处理？","🔗侵权责任如何认定？"]'
            },
            {"role": "user", "content": f"text: {text}"}
        ],
    )
    # 提取响应内容
    content = response.choices[0].message.content if response.choices else "No response"
    
    console.print(f'[blue]@recommend - recommend result: [/blue]{json.loads(content)}')

    return success_response({"recommend_items": json.loads(content)})
