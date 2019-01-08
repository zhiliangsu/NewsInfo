import time
from flask import request, render_template, jsonify, current_app, session, redirect, url_for, g
from info import get_user_data, constants, db
from info.models import User, News
from info.utils.response_code import RET
from . import admin_bp
from datetime import datetime, timedelta


# 127.0.0.1:5000/admin/news_edit?p=1
@admin_bp.route('/news_edit')
def news_edit():
    """展示新闻版式编辑页面数据"""
    """
        1.获取参数
            1.1 p:查询的页码，默认值：1 表示查询第一页的数据, user：当前用户对象
        2.校验参数
            2.1 页码的数据类型判断
        3.逻辑处理
            3.0 根据News.query.filter(查询条件).order_by(新闻创建时间降序).paginate(当前页码，每一页多少条数据，False)
                查询条件1（非必须的）：标题是否包含搜索关键字key
            3.1 将查询到新闻对象列表转换成字典列表
        4.返回值
    """
    p = request.args.get("p", 1)
    keyword = request.args.get("keywords")

    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        p = 1

    filter_list = []
    if keyword:
        filter_list.append(News.title.contains(keyword))

    news_list = []
    current_page = 1
    total_page = 1

    try:
        paginate = News.query.filter(*filter_list).order_by(News.create_time.desc())\
                    .paginate(p, constants.ADMIN_NEWS_EDIT_PAGE_MAX_COUNT, False)
        news_list = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询新闻对象异常")

    news_dict_list = []
    for news in news_list if news_list else []:
        news_dict_list.append(news.to_basic_dict())

    data = {
        "news_list": news_dict_list,
        "current_page": current_page,
        "total_page": total_page
    }

    return render_template("admin/news_edit.html", data=data)


# 127.0.0.1：5000/admin/news_review_detail?news_id=1
@admin_bp.route('/news_review_detail', methods=["POST", "GET"])
def news_review_detail():
    """返回新闻审核详情页面&新闻审核的业务逻辑"""

    # GET请求: 返回新闻审核的详情页面
    if request.method == "GET":

        news_id = request.args.get("news_id")
        # 查询新闻对象
        news = None
        try:
            news = News.query.get(news_id)
        except Exception as e:
            current_app.logger.error(e)

        return render_template("admin/news_review_detail.html", data={"news": news.to_dict() if news else None})

    # POST请求:新闻审核的业务逻辑
    """
    1.获取参数
        1.1 news_id:新闻id，action:审核的行为，reason:拒绝原因
    2.校验参数
        2.1 非空判断
        2.2 action in ["accept", "reject"]
    3.逻辑处理
        3.0 根据新闻id查询对应新闻对象，新闻存在再去审核
        3.1 审核通过：将news对象的status属性修改为：0
        3.2 审核不通过：将news对象的status属性修改为：-1，同时添加拒绝原因
        3.3 保存回数据库
    4.返回值
    """
    # 1.1 news_id:新闻id，action:审核的行为，reason:拒绝原因(非必须要传的参数)
    news_id = request.json.get("news_id")
    action = request.json.get("action")

    # 2.1 非空判断
    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")

    # 2.2 action in ["accept", "reject"]
    if action not in ["accept", "reject"]:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 3.0 根据新闻id查询对应新闻对象，新闻存在再去审核
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询新闻对象异常")

    if not news:
        return jsonify(errno=RET.NODATA, errmsg="新闻不存在")

    # 3.1 审核通过：将news对象的status属性修改为：0
    if action == "accept":
        news.status = 0
    # 3.2 审核不通过：将news对象的status属性修改为：-1，同时添加拒绝原因
    else:
        reason = request.json.get("reason")
        if reason:
            news.status = -1
            news.reason = reason
        else:
            return jsonify(errno=RET.PARAMERR, errmsg="拒绝原因不能为空")

    # 3.3 保存回数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存新闻对象异常")

    return jsonify(errno=RET.OK, errmsg="OK")


# 127.0.0.1:5000/admin/news_review?p=1
@admin_bp.route('/news_review')
def news_review():
    """展示新闻审核页面数据"""
    """
        1.获取参数
            1.1 p:查询的页码，默认值：1 表示查询第一页的数据, user：当前用户对象
        2.校验参数
            2.1 页码的数据类型判断
        3.逻辑处理
            3.0 根据News.query.filter(查询条件).order_by(新闻创建时间降序).paginate(当前页码，每一页多少条数据，False)
                查询条件1：查询未审核&审核未通过的新闻
                查询条件2（非必须的）：标题是否包含搜索关键字key
            3.1 将查询到新闻对象列表转换成字典列表
        4.返回值
    """

    # 1.1 p:查询的页码，默认值：1 表示查询第一页的数据, user：当前用户对象
    p = request.args.get("p", 1)
    keyword = request.args.get("keywords")

    # 2.1 页码的数据类型判断
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        p = 1

    # 3.0 News.query.filter(查询条件).order_by(新闻创建时间降序)进行分页查询
    news_list = []
    current_page = 1
    total_page = 1

    # 条件列表: 默认条件 --> 查询未审核&审核未通过的新闻
    filter_list = [News.status != 0]
    # 关键字搜索
    if keyword:
        # 添加标题是否包含搜索关键字key条件
        filter_list.append(News.title.contains(keyword))

    try:
        paginate = News.query.filter(*filter_list).order_by(News.create_time.desc())\
                    .paginate(p, constants.ADMIN_NEWS_PAGE_MAX_COUNT, False)
        news_list = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询用户列表对象异常")

    # 3.1 将查询到用户对象列表转换成字典列表
    news_dict_list = []
    for news in news_list if news_list else []:
        news_dict_list.append(news.to_review_dict())

    # 组织返回数据
    data = {
        "news_list": news_dict_list,
        "current_page": current_page,
        "total_page": total_page
    }

    return render_template("admin/news_review.html", data=data)


# 127.0.0.1:5000/admin/user_list?p=1
@admin_bp.route('/user_list')
def user_list():
    """展示用户列表页面数据"""
    """
        1.获取参数
            1.1 p:查询的页码，默认值：1 表示查询第一页的数据, user：当前用户对象
        2.校验参数
            2.1 页码的数据类型判断
        3.逻辑处理
            3.0 根据User.query.filter(条件用户是非管理员即可) 进行分页查询
            3.1 将查询到用户对象列表转换成字典列表
        4.返回值
    """

    # 1.1 p:查询的页码，默认值：1 表示查询第一页的数据, user：当前用户对象
    p = request.args.get("p", 1)

    # 2.1 页码的数据类型判断
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        p = 1

    # 3.0 根据User.query.filter(条件用户是非管理员即可) 进行分页查询
    user_list = []
    current_page = 1
    total_page = 1

    try:
        paginate = User.query.filter(User.is_admin == False).order_by(User.create_time.desc())\
                    .paginate(p, constants.ADMIN_USER_PAGE_MAX_COUNT, False)
        user_list = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询用户列表对象异常")

    # 3.1 将查询到用户对象列表转换成字典列表
    user_dict_list = []
    for user in user_list if user_list else []:
        user_dict_list.append(user.to_admin_dict())

    # 组织返回数据
    data = {
        "users": user_dict_list,
        "current_page": current_page,
        "total_page": total_page
    }

    return render_template("admin/user_list.html", data=data)


# 127.0.0.1:5000/admin/user_count
@admin_bp.route('/user_count')
def user_count():
    """用户统计"""
    # 查询总人数
    total_count = 0
    try:
        # 统计非管理员用户的个数
        total_count = User.query.filter(User.is_admin == False).count()
    except Exception as e:
        current_app.logger.error(e)

    # 查询月新增数
    """
    
    time.struct_time(tm_year=2019, tm_mon=1, tm_mday=5, tm_hour=16, tm_min=57, tm_sec=18, tm_wday=5, tm_yday=5, tm_isdst=0)
    
    2019-1-1号 ~ 2019-1-5
    """
    # 本月新增多少用户
    mon_count = 0
    try:
        # 获取系统当前时间
        now = time.localtime()
        # 本月的开始时间 2019-01-01
        # 下个月的开始时间 2019-02-01
        # 每一个月第一天（字符串）
        mon_begin = '%d-%02d-01' % (now.tm_year, now.tm_mon)
        # strptime：将字符串格式数据转换成时间格式数据
        mon_begin_date = datetime.strptime(mon_begin, '%Y-%m-%d')
        # 查询条件：用户的创建时间 > 大于本月的第一天： 代表就是本月新增了多少用户
        mon_count = User.query.filter(User.is_admin == False, User.create_time >= mon_begin_date).count()
    except Exception as e:
        current_app.logger.error(e)

    # 查询日新增数
    """
    今天的开始时间:2019-01-05：00：00
    今天的结束时间:2019-01-05：23：59
    """
    day_count = 0
    try:
        # 今天的开始时间的字符串
        day_begin = '%d-%02d-%02d' % (now.tm_year, now.tm_mon, now.tm_mday)
        # 转换成时间格式
        day_begin_date = datetime.strptime(day_begin, '%Y-%m-%d')
        # 查询条件： 用户的创建时间 > 今天的开始时间2019-01-05：00：00  代表：今天新增用户人数
        day_count = User.query.filter(User.is_admin == False, User.create_time > day_begin_date).count()
    except Exception as e:
        current_app.logger.error(e)

    # 查询图表信息
    # 获取到当天00:00:00时间

    now_date = datetime.strptime(datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d')
    # 定义空数组，保存数据
    active_date = []
    active_count = []

    """
    now_date:获取当前的时间
    今天开始时间：2019-01-05  - 减去0天
    今天结束时间：2019-01-05：23：59 = 开始时候 + 1天
    
    上一天开始时间：2019-01-05  - 减去1天  =  2019-01-04
    上一天结束时间：2019-01-04：23：59 = 开始时候 + 1天
     .
     .
     .
    一个之前开始时间：2019-01-05  - 减去30天  =  2018-12-05
    一个之前开始结束：2018-12-05：23：59 = 开始时候 + 1天
    
    统计过去一个月每一天用户活跃量
    
    """

    # 依次添加数据，再反转
    for i in range(0, 31):
        # 一天的开始时间
        begin_date = now_date - timedelta(days=i)
        # 一天的结束时间 = 开始时间 + 1天
        # now_date - timedelta(days=i) + timedelta(days=1)
        # begin_date + timedelta(days=1)
        end_date = now_date - timedelta(days=(i - 1))
        active_date.append(begin_date.strftime('%Y-%m-%d'))
        count = 0
        try:
            # 查询条件： 用户最后一次登录时间 >= 一天的开始时间  and 用户最后一次登录时间 < 一天的结束时间
            # 查询条件： 一天的开始时间 <= 用户最后一次登录时间 <  一天的结束时间
            # 每一天的用户活跃量
            count = User.query.filter(User.is_admin == False, User.last_login >= begin_date,
                                      User.last_login < end_date).count()
        except Exception as e:
            current_app.logger.error(e)
        # 将活跃人数添加到列表
        active_count.append(count)

    # 日期和活跃人数都反转
    active_date.reverse()
    active_count.reverse()

    data = {"total_count": total_count, "mon_count": mon_count, "day_count": day_count, "active_date": active_date,
            "active_count": active_count}

    return render_template('admin/user_count.html', data=data)


# 127.0.0.1:5000/admin/
@admin_bp.route('/')
@get_user_data
def admin_index():
    """管理员首页"""

    # 获取登录的管理员用户对象
    admin_user = g.user

    data = {
        "user": admin_user.to_dict() if admin_user else None
    }

    # 返回首页模板
    return render_template("admin/index.html", data=data)


# 127.0.0.1:5000/admin/login
@admin_bp.route('/login', methods=["POST", "GET"])
def admin_login():
    """管理员后台登录接口"""

    # GET请求: 返回管理员登录的模板
    if request.method == "GET":

        # 优化: 当管理员用户已登录,再次访问/admin/login接口的时候,我们应该直接引导到管理员的首页

        # 获取当前登录用户的id
        user_id = session.get("user_id")
        # 登录的用户是管理员
        is_admin = session.get("is_admin")

        # 用户登录了,而且是管理员
        if user_id and is_admin:
            # 直接引导到管理员首页
            return redirect(url_for("admin.admin_index"))

        return render_template("admin/login.html")

    # POST请求: 后台登录的逻辑处理
    """
    1.获取参数
        1.1 username:管理员用户账号，password：未加密密码
    2.校验参数
        2.1 非空判断
    3.逻辑处理
        3.0 根据name账号查询出管理员用户对象
        3.1 管理员用户的密码校验
        3.2 使用session记录管理员登录信息
    4.返回值
        登录成功
    """

    # 获取参数
    username = request.form.get("username")
    password = request.form.get("password")

    # 校验参数
    if not all([username, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")

    # 逻辑处理
    admin_user = None  # type: User
    try:
        admin_user = User.query.filter(User.is_admin == True, User.mobile == username).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询管理员用户异常")

    if not admin_user:
        return render_template("admin/login.html", errmsg="管理员用户不存在")

    if not admin_user.check_passowrd(password):
        return render_template("admin/login.html", errmsg="密码填写错误")

    # 使用session记录管理员登录信息
    session["user_id"] = admin_user.id
    session["mobile"] = admin_user.mobile
    session["nick_name"] = username
    # 记录用户对象是否是管理员
    session["is_admin"] = True

    # 转到管理员首页
    return redirect(url_for("admin.admin_index"))

