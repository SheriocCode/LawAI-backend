# -*- coding: utf-8 -*-
from flask import Flask

from config import AppConfig
from utils.db import init_db, cors

from routes.user_routes import user_bp
from routes.ai_routes import ai_bp


if __name__ == "__main__":
    app = Flask(__name__)
    app.config.from_object(AppConfig)

    # 初始化扩展
    init_db(app)
    cors(app)

    # 注册蓝图 
    app.register_blueprint(user_bp)
    app.register_blueprint(ai_bp)

    app.run(debug=True)