from info import constants
from info.models import News, Category
from info.modules.index import index_bp
from flask import current_app, render_template,jsonify, request, g
from info.utils.common import get_user_data
from info.utils.response_code import RET


# get请求地址: /news_list?cid=1&p=1&per_page=10
@index_bp.route('/news_list')
def get_news_list():
    """获取首页新闻列表数据接口"""
    """
    1.获取参数
        1.1 cid:分类id, p:当前页码,默认值:1表示第一页数据, per_page:每一页多少条数据,默认值:10
    2.参数校验
        2.1 cid非空判断
        2.2 将数据int强制转换类型
    3.逻辑处理
        3.1 根据cid作为查询条件,新闻的时间降序排序,进行分页查询
        3.2 将新闻对象列表转换成字典列表
    4.返回值
    """

    # 1.获取参数
    cid = request.args.get("cid")
    p = request.args.get("page", 1)
    per_page = request.args.get("per_page", 10)

    # 2.参数校验
    if not cid:
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")

    try:
        cid = int(cid)
        p = int(p)
        per_page = int(per_page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数类型错误")

    # 3.逻辑处理
    news_list = []
    current_page = 1
    total_page = 1

    # 查询条件列表
    filter_list = []
    if cid != 1:
        # 将查询条件添加到列表中
        filter_list.append(News.category_id == cid)

    # 3.1 根据cid作为查询条件, 新闻的时间降序排序, 进行分页查询
    # paginate(): 参数1: 当前页码, 参数2: 每一页多少条数据, 参数3: 不需要错误参数,使用try捕获
    try:
        paginate = News.query.filter(*filter_list).order_by(News.create_time.desc()).paginate(p, per_page, False)
        # 获取所有数据
        news_list = paginate.items
        # 获取当前页码
        current_page = paginate.page
        # 获取总页数
        total_page = paginate.pages

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询新闻列表数据异常")

    # 将新闻对象列表转换成字典列表
    news_dict_list = []
    for news in news_list if news_list else []:
        news_dict_list.append(news.to_dict())

    # 组织返回数据
    data = {
        "news_list": news_dict_list,
        "current_page": current_page,
        "total_page": total_page
    }

    return jsonify(errno=RET.OK, errmsg="查询新闻列表数据成功", data=data)


@index_bp.route('/')
@get_user_data
def index():
    # -----------------1.用户登录成功,查询用户基本信息展示---------------
    user = g.user

    # 3. 将用户对象转成字典
    """
    if user:
        user_dict = user.to_dict()
    """
    user_dict = user.to_dict() if user else None

    # -----------------2.查询新闻点击排行数据展示---------------
    try:
        news_rank_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询新闻对象异常")

    news_dict_list = []
    # 将新闻列表对象列表转成字典列表
    for news in news_rank_list if news_rank_list else []:
        news_dict_list.append(news.to_dict())

    # -----------------3.查询新闻分类数据展示---------------
    try:
        categories = Category.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询分类对象异常")

    category_dict_list = []
    # 将分类列表对象列表转成字典列表
    for category in categories if categories else []:
        category_dict_list.append(category.to_dict())

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
        "user_info": user_dict,
        "click_news_list": news_dict_list,
        "categories": category_dict_list
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
