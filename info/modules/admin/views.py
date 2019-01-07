from flask import request, render_template, jsonify, current_app, session, redirect, url_for
from info.models import User
from info.utils.response_code import RET
from . import admin_bp


# 127.0.0.1:5000/admin/
@admin_bp.route('/')
def admin_index():
    """管理员首页"""
    # 返回首页模板
    return render_template("admin/index.html")


# 127.0.0.1:5000/admin/login
@admin_bp.route('/login', methods=["POST", "GET"])
def admin_login():
    """管理员后台登录接口"""

    # GET请求: 返回管理员登录的模板
    if request.method == "GET":
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

    # 使用session记录管理员登录信息
    session["user_id"] = admin_user.id
    session["mobile"] = admin_user.mobile
    session["nick_name"] = username
    # 记录用户对象是否是管理员
    session["is_admin"] = True

    # 转到管理员首页
    return redirect(url_for("admin.admin_index"))

