from flask import g, render_template, request, jsonify, session, current_app
from info import get_user_data, db, constants
from info.models import Category, News
from info.utils.pic_storage import pic_storage
from info.utils.response_code import RET
from . import profile_bp


# 127.0.0.1:5000/user/news_release ---> 发布新闻的页面展示&发布新闻的逻辑处理
@profile_bp.route('/news_release', methods=["POST", "GET"])
@get_user_data
def news_release():
    """发布新闻的页面展示&发布新闻的逻辑处理"""

    # GET请求: 发布新闻的页面展示,同时将分类数据返回
    if request.method == "GET":
        # 1.查询所有分类数据
        categories = []
        try:
            categories = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="查询分类对象异常")

        # 2.将分类列表对象转换成字典对象
        category_dict_list = []
        for category in categories if categories else []:
            category_dict_list.append(category.to_dict())

        # 移除最新分类
        category_dict_list.pop(0)

        return render_template("profile/user_news_release.html", data={"categories": category_dict_list})

    # POST请求: 发布新闻的逻辑处理
    """
    1.获取参数(表单提取数据)
        1.1 title:新闻标题，cid:新闻分类id，digest:新闻的摘要，
            index_image:新闻主图片，content:新闻的内容，user:当前用户对象, source:新闻来源，个人发布
    2.校验参数
        2.1 非空判断
    3.逻辑处理
        3.0 新闻主图片保存到七牛云
        3.1 创建新闻对象，给各个属性赋值，保存回数据库
    4.返回值
    """

    # 1.获取参数(表单提取数据)
    params_dict = request.form
    title = params_dict.get("title")
    cid = params_dict.get("category_id")
    digest = params_dict.get("digest")
    content = params_dict.get("content")
    index_image = request.files.get("index_image")
    user = g.user
    source = "个人发布"

    # 2.校验参数
    if not all([title, cid, digest, content, index_image]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")

    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    # cid类型转换
    try:
        cid = int(cid)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="分类id格式错误")

    # 3.0 新闻主图片保存到七牛云
    pic_data = None

    # 读取用户发布新闻时上传的图片数据
    try:
        pic_data = index_image.read()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="读取图片数据异常")

    # 把图片上传到七牛云
    try:
        pic_name = pic_storage(pic_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="上传图片到七牛云异常")

    # 3.1 创建新闻对象，给各个属性赋值，保存回数据库
    news = News()
    news.title = title
    news.category_id = cid
    news.digest = digest
    news.content = content
    news.index_image_url = constants.QINIU_DOMIN_PREFIX + pic_name
    news.source = source
    news.user_id = user.id
    # 状态0: 已通过  状态1: 审核中  状态-1: 未通过
    news.status = 1

    try:
        db.session.add(news)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存新闻对象异常")

    return jsonify(errno=RET.OK, errmsg="新闻发布成功")


# 127.0.0.1:5000/user/collection?p=1
@profile_bp.route('/collection')
@get_user_data
def get_collection():
    """获取用户的收藏新闻列表数据(分页)"""
    """
    1.获取参数
        1.1 p:查询的页码，默认值：1 表示查询第一页的数据, user：当前用户对象
    2.校验参数
        2.1 页码的数据类型判断
    3.逻辑处理
        3.0 根据user.collection_news查询对象进行分页查询
        3.1 将查询到新闻对象列表转换成字典列表
    4.返回值
    """
    # 1.1 p:查询的页码，默认值：1 表示查询第一页的数据, user：当前用户对象
    p = request.args.get("p", 1)
    user = g.user

    # 2.1 页码的数据类型判断
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        p = 1

    # 3.0 根据user.collection_news查询对象进行分页查询
    """
    user.collection_news使用了lazy="dynamic"修饰:
        1.如果真实用到数据: user.collection_news返回的是新闻对象列表数据
        2.如果只是查询: user.collection_news返回的是查询对象
    """
    news_list = []
    current_page = 1
    total_page = 1
    # 只有用户登录的情况下再查询用户收藏数据
    if user:
        try:
            paginate = user.collection_news.paginate(p, constants.USER_COLLECTION_MAX_NEWS, False)
            # 当前页所有数据
            news_list = paginate.items
            # 当前页码
            current_page = paginate.page
            # 总页数据
            total_page = paginate.pages
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="查询用户收藏的新闻对象异常")

    # 3.1 将查询到新闻对象列表转换成字典列表
    news_dict_list = []
    for news in news_list if news_list else []:
        news_dict_list.append(news.to_review_dict())

    # 组织返回数据
    data = {
        "collections": news_dict_list,
        "current_page": current_page,
        "total_page": total_page
    }

    # 4.返回值
    return render_template("profile/user_collection.html", data=data)


# 127.0.0.1:5000/user/pass_info ---> 展示修改密码页面&密码提交修改
@profile_bp.route('/pass_info', methods=["POST", "GET"])
@get_user_data
def pass_info():
    """展示修改密码页面&密码提交修改"""

    # GET请求: 返回密码修改的页面
    if request.method == "GET":
        return render_template("profile/user_pass_info.html")

    # POST请求: 提交新旧密码并进行修改保存到数据库
    """
    1.获取参数
        1.1 old_password: 旧密码，new_password:新密码，user:当前登录的用户对象
    2.校验参数
        2.1 非空判断
    3.逻辑处理
        3.0 调用user对象上的check_passowrd方法对旧密码进行校验
        3.1 将新密码赋值给user对象password属性，内部会自动加密
        3.2 保存回数据库
    4.返回值
    """

    # 1.获取参数
    old_password = request.json.get("old_password")
    new_password = request.json.get("new_password")
    user = g.user

    # 2.校验参数
    if not all([old_password, new_password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")

    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    # 3.逻辑处理
    if not user.check_passowrd(old_password):
        return jsonify(errno=RET.PWDERR, errmsg="密码填写错误")

    user.password = new_password

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存用户密码异常")

    return jsonify(errno=RET.OK, errmsg="修改密码成功")


# 127.0.0.1:5000/user/pic_info ---> 展示修改头像页面&头像数据修改
@profile_bp.route('/pic_info', methods=["POST", "GET"])
@get_user_data
def pic_info():
    """展示修改头像页面&头像数据修改"""

    # 获取当前登录用户
    user = g.user

    # GET请求: 返回模板页面,展示修改头像页面
    if request.method == "GET":
        return render_template("profile/user_pic_info.html", data={"user": user.to_dict() if user else None})

    # POST请求: 提交头像数据并修改保存
    """
    1.获取参数
        1.1 avatar:上传的图片数据, user:当前用户对象
    2.校验参数
        2.1 非空判断
    3.逻辑处理
        3.0 调用工具类将图片数据上传带七牛云
        3.1 将返回的图片名称给予avatar_url赋值，并保存回数据库
        3.2 将图片的完整url返回
    4.返回值
    """

    # 1.1 avatar:上传的图片数据, user:当前用户对象
    avatar = request.files.get("avatar")

    # ?
    avatar_data = None
    try:
        avatar_data = avatar.read()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="图片二进制数据读取失败")

    # 2.1 非空判断
    if not avatar_data:
        return jsonify(errno=RET.PARAMERR, errmsg="图片数据为空")

    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    # 3.0 调用工具类将图片数据上传带七牛云
    try:
        pic_name = pic_storage(avatar_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="上传图片到七牛云异常")

    # 3.1 将返回的图片名称给予avatar_url赋值，并保存回数据库
    user.avatar_url = pic_name

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存用户头像数据异常")

    # 3.2 将图片的完整url返回
    full_url = constants.QINIU_DOMIN_PREFIX + pic_name

    return jsonify(errno=RET.OK, errmsg="上传图片成功", data={"avatar_url": full_url})


# 127.0.0.1:5000/user/base_info ---> 用户基本资料页面
@profile_bp.route('/base_info', methods=["POST", "GET"])
@get_user_data
def base_info():
    """用户基本资料页面"""

    # 获取当前登录用户对象
    user = g.user

    # GET请求: 返回模板页面,展示用户基本资料
    if request.method == "GET":
        data = {"user_info": user.to_dict() if user else None}
        return render_template("profile/user_base_info.html", data=data)

    # POST请求: 修改用户基本资料
    """
    1.获取参数
        1.1 user: 当前登录用户对象， signature:个性签名，nick_name:昵称，gender:性别
    2.校验参数
        2.1 非空判断
        2.2 gender in ["MAN", "WOMAN"]
    3.逻辑处理
        3.0 将当前用户各个属性重新赋值 ，保存到数据库即可
    4.返回值
        登录成功
    """

    # 1.1 user: 当前登录用户对象， signature:个性签名，nick_name:昵称，gender:性别
    signature = request.json.get("signature")
    nick_name = request.json.get("nick_name")
    gender = request.json.get("gender")

    # 2.1 非空判断
    if not all([signature, nick_name, gender]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")

    # 2.2 gender in ["MAN", "WOMAN"]
    if gender not in ["MAN", "WOMAN"]:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 3.0 将当前用户各个属性重新赋值 ，保存到数据库即可
    user.signature = signature
    user.nick_name = nick_name
    user.gender = gender

    # 注意: 修改了nick_name, 会话对象session中保存的数据也需要更新
    session["nick_name"] = nick_name

    # 将上述修改操作保存到数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="修改用户对象基本数据异常")

    # 4.返回值
    return jsonify(errno=RET.OK, errmsg="修改用户基本数据成功")


# 127.0.0.1:5000/user/info ---> 个人中心页面
@profile_bp.route('/info')
@get_user_data
def user_info():
    """展示个人中心页面"""
    user = g.user
    data = {
        "user_info": user.to_dict() if user else None
    }
    return render_template("profile/user.html", data=data)
