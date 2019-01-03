from info.models import User
from info.modules.index import index_bp
from flask import current_app, render_template, session, jsonify

from info.utils.response_code import RET


@index_bp.route('/')
def index():
    # -----------------用户登录成功,查询用户基本信息展示---------------
    # 1. 获取用户的id
    user_id = session.get("user_id")
    # 先声明防止局部变量不能访问
    user = None
    if user_id:
        # 2. 根据user_id查询当前登录的用户对象
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="查询用户对象异常")

    # 3. 将用户对象转成字典
    """
    if user:
        user_dict = user.to_dict()
    """
    user_dict = user.to_dict() if user else None

    # 4. 组织响应数据
    """
    数据格式:
    data = {
        "user_info": {
            "id": self.id,
            "nick_name": self.nick_name
        }
    }
    前端使用方式: data.user_info.nick_name
    """
    data = {
        "user_info": user_dict
    }

    return render_template("news/index.html", data=data)


@index_bp.route('/favicon.ico')
def favicon():
    """
    返回网站图标

    Function used internally to send static files from the static
        folder to the browser
    内部用来发送静态文件到浏览器的方法
    """
    return current_app.send_static_file("news/favicon.ico")
