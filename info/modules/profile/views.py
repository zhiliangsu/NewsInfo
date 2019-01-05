from flask import g, render_template, request
from info import get_user_data
from . import profile_bp


# 127.0.0.1:5000/user/baseinfo ---> 用户基本资料页面
@profile_bp.route('/baseinfo', methods=["POST", "GET"])
@get_user_data
def baseinfo():
    """用户基本资料页面"""

    # GET请求: 返回模板页面,展示用户基本资料
    if request.method == "GET":
        user = g.user
        data = {
            "user_info": user.to_dict() if user else None
        }

        return render_template("profile/user_base_info.html", data=data)

    # POST请求: 修改用户基本资料


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
