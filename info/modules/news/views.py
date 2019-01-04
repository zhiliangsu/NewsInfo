from info import constants
from info.models import News
from info.utils.common import get_user_data
from info.utils.response_code import RET
from . import news_bp
from flask import render_template, current_app, jsonify, g, abort


# 127.0.0.1:5000/news/news_id  news_id:新闻对应的id地址
@news_bp.route('/<int:news_id>')
@get_user_data
def news_detail(news_id):
    """新闻详情页展示"""

    # -----------------1.用户登录成功,查询用户基本信息展示---------------
    # 使用g对象传递user对象数据
    user = g.user

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

    # -----------------3.根据新闻id查询新闻详情数据展示----------------------
    news_obj = None
    if news_id:
        try:
            news_obj = News.query.get(news_id)
        except Exception as e:
            current_app.logger.error(e)
            abort(404)
            return jsonify(errno=RET.DBERR, errmsg="查询新闻对象异常")

    # 新闻对象转字典
    news_dict = news_obj.to_dict() if news_obj else None

    # -----------------4.查询当前登录用户是否收藏过当前新闻----------------------
    # 标识当前用户是否收藏当前新闻, 默认值:false没有收藏
    is_collected = False

    # user.collection_news: 当前用户对象收藏的新闻列表
    # news_obj: 当前新闻对象
    # 判断当前新闻对象是否在当前用户对象的新闻收藏类别中
    if news_obj in user.collection_news:
        # 标识当前用户已经收藏该新闻
        is_collected = True

    # 组织响应数据
    data = {
        "user_info": user_dict,
        "click_news_list": news_dict_list,
        "news": news_dict,
        "is_collected": is_collected
    }
    return render_template("news/detail.html", data=data)
