# LawAI-backend

## 环境配置
1. `python version : 3.9`
2. 虚拟环境创建（conda环境/venv虚拟环境）
3. `pip install -r requirements.txt`

## 数据库配置
> 数据库仓库 https://github.com/SheriocCode/LawAI-dataend
1. 数据库转换：控制台输入 `sqlite3 database.db < database_dump.sql` 命令将 sql 文件导入到 sqlite3 数据库中
2. 将得到的`database.db`放到`LawAI-backend/instance`目录下
3. **(可选)** `LawAI-dataend`数据库发生更新时，重新生成`database.db`文件，替换`LawAI-backend/instance`目录下的`database.db`文件

## 配置文件
1. `LawAI-backend/`目录下添加配置文件`.env`文件

## 项目启动👉
1. `LawAI-backend/`目录下输入 `python app.py` 启动项目