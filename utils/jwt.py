from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import jwt
from functools import wraps
from config import AppConfig

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')  # 从请求头获取 JWT
        if not token:
            return jsonify({
                "code": 403,
                "message": 'Token is missing'
            })
        
        if token and token.startswith('Bearer '):
            token = token.split(' ')[1]  # 去掉 Bearer 前缀

        try:
            # 解码 JWT
            data = jwt.decode(token, AppConfig.JWT_SECRET_KEY, algorithms=['HS256'])
            # 将解码后的数据添加到请求中，以便后续处理
            request.user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({
                "code": 403,
                "message": "Token has expired"
            })
        except jwt.InvalidTokenError:
            return jsonify({
                "code": 403,
                "message": "Invalid token"
            })
        return f(*args, **kwargs)

    return decorated

def generate_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=1)  # 令牌有效期为 1 小时
    }
    token = jwt.encode(payload, AppConfig.JWT_SECRET_KEY, algorithm='HS256')
    return token