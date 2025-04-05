from flask import Blueprint, request
from utils.result import error_response, success_response
from utils.jwt import generate_token, token_required
from db import user_register, user_login
from db import get_user_by_id, update_user_info

user_bp = Blueprint('user', __name__)

# 用户注册
@user_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    success, msg = user_register(username, password)

    if not success:
        return error_response(msg)
    
    return success_response({
        "register_status": "success"
    })

# 用户登录
@user_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    success, user = user_login(username)
    if not success or user.password != password:
        return error_response("用户不存在或密码错误!")
    
    token = generate_token(user.id)
    
    return success_response({
        "token": token,
        "user_info":{
            "user_id": user.id,
            "username": user.username,
            "avatar": user.avatar,
        }
    })

# 退出登录
@user_bp.route('/logout', methods=['GET'])
@token_required
def logout():
    return success_response({})


# 用户信息
@user_bp.route('/user/profile', methods=['get'])
@token_required
def user_profile():
    user_id = request.user_id
    success, user = get_user_by_id(user_id)
    # 构建用户信息字典
    res = {
        "user_id": user.id,
        "username": user.username,
        "avatar": user.avatar if user.avatar else None,  # 如果 avatar 为空，返回 None
        "signature": user.signature if user.signature else None,  # 如果 signature 为空，返回 None
        "gender": user.gender if user.gender else None,  # 如果 gender 为空，默认为 "male"
        "register_date": user.register_date.strftime("%Y-%m-%d")  # 将 datetime 转换为 ISO 8601 格式的字符串
    }

    return success_response(res)

# 修改用户信息
@user_bp.route('/user/info_change', methods=['POST'])
@token_required
def user_info_change():
    user_id = request.user_id
    # 获取表单数据
    data = request.json

    username = data.get('username')
    avatar = data.get('avatar')
    password = data.get('password')
    signature = data.get('signature')
    gender = data.get('gender')

    success, updated_user = update_user_info(user_id, username, avatar, password, signature, gender)
    res = {
        "user_id": updated_user.id,
        "username": updated_user.username,
        "avatar": updated_user.avatar if updated_user.avatar else None,  # 如果 avatar 为空，返回 None
        "signature": updated_user.signature if updated_user.signature else None,  # 如果 signature 为空，返回 None
        "gender": updated_user.gender if updated_user.gender else None,  # 如果 gender 为空，默认为 "male"
        "register_date": updated_user.register_date.strftime("%Y-%m-%d")  # 将 datetime 转换为 ISO 8601 格式的字符串
    }

    return success_response(res)


