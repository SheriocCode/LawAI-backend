from flask import Blueprint, request
from utils.result import error_response, success_response
from utils.jwt import generate_token, token_required
from db import user_register, user_login

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
@user_bp.route("/logout", methods=["GET"])
@token_required
def logout():
    return success_response({})
