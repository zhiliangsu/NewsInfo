from info import constants, db
from info.models import News, Comment
from info.utils.common import get_user_data
from info.utils.response_code import RET
from . import news_bp
from flask import render_template, current_app, jsonify, g, abort, request


# POST请求地址: 127.0.0.1:5000/news/news_comment  参数由请求体携带
@news_bp.route('/news_comment', methods=["POST"])
@get_user_data
def news_comment():
    """发布(主，子)评论的后端接口"""

    """
    1.获取参数
        1.1 news_id: 新闻id，user:当前登录的用户对象，comment:新闻评论的内容，parent_id:区分主评论，子评论参数
    2.参数校验
        2.1 非空判断
    3.逻辑处理
        3.1 根据news_id查询当前新闻对象
        3.2 创建评论对象，并给各个属性赋值，保存回数据库
    4.返回值
    """

    # 1.获取参数
    params_dict = request.json
    news_id = params_dict.get("news_id")
    content = params_dict.get("comment")
    parent_id = params_dict.get("parent_id")
    user = g.user

    # 2.参数校验
    if not all([news_id, content]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")

    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    # 3.逻辑处理
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询新闻对象异常")

    if not news:
        return jsonify(errno=RET.NODATA, errmsg="新闻对象不存在")

    # 创建评论对象,并给各个属性赋值,保存回数据库
    comment_obj = Comment()
    comment_obj.user_id = user.id
    comment_obj.news_id = news_id
    comment_obj.content = content
    # 区分主评论和子评论
    if parent_id:
        # 代表是一条子评论
        comment_obj.parent_id = parent_id

    # 保存回数据库
    try:
        db.session.add(comment_obj)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存评论对象异常")

    # 4.返回值
    return jsonify(errno=RET.OK, errmsg="发布评论成功", data=comment_obj.to_dict())


# POST请求地址: 127.0.0.1:5000/news/news_collect  参数由请求体携带
@news_bp.route('/news_collect', methods=["POST"])
@get_user_data
def news_collect():
    """新闻收藏、取消收藏的后端接口"""
    """
    1.获取参数
        1.1 news_id:当前新闻的id，user:当前登录的用户对象，action:收藏，取消收藏的行为
    2.参数校验
        2.1 非空判断
        2.2 action in ["collect", "cancel_collect"]
    3.逻辑处理
        3.1 根据新闻id查询当前新闻对象，判断新闻是否存在
        3.2 收藏：将新闻对象添加到user.collection_news列表中
        3.3 取消收藏：将新闻对象从user.collection_news列表中移除
    4.返回值
    """

    # 1.获取参数
    params_dict = request.json
    news_id = params_dict.get("news_id")
    action = params_dict.get("action")
    user = g.user

    # 2.参数校验
    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")

    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    if action not in ["collect", "cancel_collect"]:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 3.逻辑处理
    news_obj = None
    try:
        news_obj = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询新闻对象异常")

    if not news_obj:
        return jsonify(errno=RET.NODATA, errmsg="新闻不存在")

    if action == "collect":
        user.collection_news.append(news_obj)
    else:
        # 新闻已经被用户收藏的情况才允许取消收藏
        if news_obj in user.collection_news:
            user.collection_news.remove(news_obj)

    # 将数据提交数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存新闻收藏数据异常")

    # 4.返回值
    return jsonify(errno=RET.OK, errmsg="收藏操作成功")


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

    # 将新闻对象的点击量累加
    news_obj.clicks += 1

    # 新闻对象转字典
    news_dict = news_obj.to_dict() if news_obj else None

    # -----------------4.查询当前登录用户是否收藏过当前新闻----------------------
    # 标识当前用户是否收藏当前新闻, 默认值:false没有收藏
    is_collected = False

    # 防止退出登录后,user.collection_news没有值导致报错
    if user:
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
