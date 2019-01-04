from info import constants
from info.models import User, News
from info.utils.response_code import RET
from . import news_bp
from flask import render_template, session, current_app, jsonify


# 127.0.0.1:5000/news/news_id  news_id:新闻对应的id地址
@news_bp.route('/<int:news_id>')
def news_detail(news_id):
    """新闻详情页展示"""

    # -----------------1.用户登录成功,查询用户基本信息展示---------------
    # 1. 获取用户的id
    user_id = session.get("user_id")

    # 2. 根据user_id查询当前登录的用户对象
    user = None
    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询用户对象异常")

    # 3. 将用户对象转成字典
    user_dict = user.to_dict() if user else None

    # -----------------2.查询新闻点击排行数据展示----------------------
    try:
        news_rank_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询新闻对象异常")

    # 新闻对象列表转化成字典列表
    news_dict_list = []
    for news in news_rank_list if news_rank_list else None:
        news_dict_list.append(news.to_dict())

    # 组织响应数据
    data = {
        "user_info": user_dict,
        "click_news_list": news_dict_list
    }
    return render_template("news/detail.html", data=data)
