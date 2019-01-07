from flask import request, render_template
from . import admin_bp


# 127.0.0.1:5000/admin/login
@admin_bp.route('/login', methods=["POST", "GET"])
def admin_login():
    """管理员后台登录接口"""

    # GET请求: 返回管理员登录的模板
    if request.method == "GET":
        return render_template("admin/login.html")

    # POST请求: 后台登录的逻辑处理
